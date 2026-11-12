"""Freewill's own model, Freewill 1.8B-V: one model that reads, looks at images and watches videos.

It is assembled from two open models and grown by Freewill: Qwen3 1.7B for
language (Apache-2.0), the vision tower of SigLIP2 base for the eye
(Apache-2.0), a bridge between them that Freewill trains, low-rank adapters,
and whole decoder layers that Freewill adds. About 1.82 billion parameters at
birth, growing up to a ceiling the person chooses (capacity.py); the exact count is computed from the
tensors (`FreewillVLM.count()`).

What it knows at birth comes from the pretraining of those open models, done
by their authors; training it from zero is possible with the same code
(`build(init="random")`) but needs hundreds of hours of data-centre GPUs, see
docs/OWN_MODEL.md. Nothing here measures or implies experience.

    model.py      the architecture, growth, adapters, inputs and scoring
    books.py      public-domain books and the person's own files, as passages
    synthetic.py  drawn images and videos with exactly known answers, and controls
    train.py      stages, measurement on held-out data, keep-or-refuse, ledger, checkpoints
    pipeline.py   the whole course: grow, read, see, watch
    capacity.py   the ceiling the person chooses, and what each size asks of a computer
    store.py      where the model lives on this computer, and fetching its two bases

Needs PyTorch and Transformers (the `lora` extra); huggingface_hub to fetch the bases.
"""
