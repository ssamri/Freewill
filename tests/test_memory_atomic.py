"""Concurrent UI readers must never see a half-written memory or index."""

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from freewill.core.kernel import KernelViolation
from freewill.core.memory import Memory, MemoryStore


@pytest.mark.parametrize("destination", ["memory", "compartment_index", "top_index"])
def test_readers_see_complete_files_during_an_atomic_write(tmp_path, monkeypatch, destination):
    store = MemoryStore(tmp_path / "memory")
    original = store.add(Memory("Original", "Original summary", body="Old complete account."))
    target = {
        "memory": store.root / f"{original.id}.md",
        "compartment_index": store.root / "moments" / "index.md",
        "top_index": store.root / "index.md",
    }[destination].resolve()
    old_text = target.read_text(encoding="utf-8")
    updated = store.open(original.id)
    updated.title, updated.summary, updated.body = "Updated", "Updated summary", "New complete account."
    new_memory = Memory("New", "New summary", body="A second complete account.")
    temporary_ready, allow_replace = threading.Event(), threading.Event()
    real_replace = Path.replace
    staged = []

    def pause_before_replace(source, destination_path):
        if Path(destination_path).resolve() == target:
            staged.append(source)
            temporary_ready.set()
            if not allow_replace.wait(timeout=10):
                raise TimeoutError("test did not release the staged memory write")
        return real_replace(source, destination_path)

    monkeypatch.setattr(Path, "replace", pause_before_replace)
    write = (lambda: store.add(new_memory)) if destination == "top_index" else (lambda: store.save(updated))
    with ThreadPoolExecutor(max_workers=1) as executor:
        writer = executor.submit(write)
        try:
            assert temporary_ready.wait(timeout=10), "writer never reached its atomic replacement"
            assert staged[0].parent == target.parent
            assert staged[0].suffix != ".md"
            assert staged[0].read_text(encoding="utf-8") != old_text
            # A separate reader can still parse every published memory while
            # the writer has a complete, unpublished replacement staged.
            reader = MemoryStore(store.root)
            assert target.read_text(encoding="utf-8") == old_text
            expected_ids = {original.id, "moments/new"} if destination == "top_index" else {original.id}
            assert set(reader.ids()) == expected_ids
            assert {memory.id for memory in reader.headers()} == expected_ids
            expected_body = "Old complete account." if destination in ("memory", "top_index") else updated.body
            assert reader.open(original.id).body == expected_body
        finally:
            allow_replace.set()
        writer.result(timeout=10)

    assert target.read_text(encoding="utf-8") != old_text
    assert not list(store.root.rglob("*.tmp"))
    if destination != "top_index":
        assert store.open(original.id).body == updated.body


def test_failed_replacement_keeps_the_previous_memory_and_removes_the_temporary_file(tmp_path, monkeypatch):
    store = MemoryStore(tmp_path / "memory")
    memory = store.add(Memory("Original", "Summary", body="Original account."))
    target = (store.root / f"{memory.id}.md").resolve()
    old_text = target.read_text(encoding="utf-8")
    memory.body = "Replacement account."
    real_replace = Path.replace

    def fail_memory_replacement(source, destination):
        if Path(destination).resolve() == target:
            raise OSError("simulated replacement failure")
        return real_replace(source, destination)

    monkeypatch.setattr(Path, "replace", fail_memory_replacement)
    with pytest.raises(OSError, match="simulated replacement failure"):
        store.save(memory)

    assert target.read_text(encoding="utf-8") == old_text
    assert store.open(memory.id).body == "Original account."
    assert store.ids() == [memory.id]
    assert not list(store.root.rglob("*.tmp"))


def test_a_compartment_from_an_altered_memory_cannot_write_an_index_outside_the_life(tmp_path):
    store = MemoryStore(tmp_path / "individual.life" / "memory")
    memory = store.add(Memory("Original", "Summary", body="Account."))
    path = store.root / f"{memory.id}.md"
    # Simulate a portable life whose readable memory header was altered.
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        f"compartment: {json.dumps(memory.compartment)}",
        'compartment: "../../escape"',
    )
    path.write_text(text, encoding="utf-8")

    with pytest.raises(KernelViolation, match="outside the life file"):
        store.save(store.open(memory.id))

    assert not (tmp_path / "escape").exists()
    assert not list(store.root.rglob("*.tmp"))
