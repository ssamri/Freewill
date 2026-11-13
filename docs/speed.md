# Speed of the local engines

**English** · [Français](speed.fr.md)

How fast Freewill's local engines think on a processor, what was tried to make them faster, and what was kept. Every figure below comes from the workflow `speed of the local engines` (`.github/workflows/speed-bench.yml`, `tools/speed_bench.py`), run 43287951339 of 12 November 2026, unless another run is named. Nothing here is an estimate.

## Where the ideas come from

From reading [colibri](https://github.com/JustVugg/colibri) (Apache 2.0, by Vincenzo Fornaro). Its main idea is to run very large mixture-of-experts models (hundreds of billions of parameters) on an ordinary computer: the part every token uses stays in memory, and the experts are read from the disk when the model asks for them. **That idea does not apply to Freewill's models**: Qwen3 1.7B, SmolVLM2 2.2B and Freewill 1.8B-V are small, dense (every parameter is used for every token) and already fit in memory. Three smaller ideas could apply, and were measured:

1. keep in memory what every thought reads (the being's instructions);
2. compute with one thread per physical core;
3. drafting by looking back ("prompt lookup", n-gram drafts), checked in one pass of the model.

No code was taken from colibri. llama.cpp, which Freewill already ships, implements 2 and 3; 1 is written for Freewill 1.8B-V in `freewill/vlm/model.py`.

## How it was measured

A being is born and spoken to in English and in French through the real life loop, and left to think for a while. The 14 requests it made (its instructions, about 3,400 characters, and each situation) are recorded, then replayed the same way on every configuration, greedy (temperature 0), so that answers can be compared token for token. Machines: GitHub runners with 4 logical cores and 2 physical cores (AMD EPYC), 16 GB of memory, no graphics card, Linux and Windows Server 2025.

## Freewill 1.8B-V (PyTorch)

The first 6 requests, 96 tokens per answer, Linux. Seconds per answer, the median of the 6.

| Configuration | Per answer | First token (reading) | Same answers as "before" |
|---|---|---|---|
| bfloat16, instructions read every time (**before**) | 89.3 s | 60.3 s | reference |
| bfloat16, instructions read once and kept | 52.6 s | 29.4 s | **1 of 6** |
| float32, instructions read every time | 39.1 s | 13.4 s | reference |
| float32, instructions read once and kept (**now**) | 31.3 s | 7.0 s | **6 of 6** |

From the old default to the new one, an answer went from 89.3 s to 31.3 s (2.9 times faster), and the wait before the first word from 60.3 s to 7.0 s. An earlier run on another runner of the same kind (run 43245499469) gave the same order: 6 to 7 times longer to read in bfloat16 than in float32, 3.5 times longer per answer.

What was kept:

- **float32 by default** where the processor has no bfloat16 of its own (most PCs: without AVX512-BF16 or AMX, PyTorch converts each bfloat16 weight on the fly) and the memory holds it (12 GB or more; float32 takes about 8 GB, bfloat16 about 4 GB). Otherwise bfloat16. `FREEWILL_OWN_DTYPE` overrides it.
- **Instructions read once and kept**, in float32: identical answers in 6 of 6. In bfloat16 the answers were not the same in 5 of 6 (rounding differs when the text is read in two pieces), so there it stays off unless `FREEWILL_OWN_REUSE=1`. The cache is dropped as soon as the weights may change (a night of training).

## Qwen3 1.7B through llama.cpp (b12306)

All 14 requests, two rounds, seconds for the 14 together.

| Configuration | Linux, round 1 / 2 | Windows, round 1 / 2 | Same answers |
|---|---|---|---|
| every logical core but one (3 threads, **before and now**) | 257.8 / 250.1 | 458.0 / 455.3 | reference |
| physical cores (2 threads) | 240.3 / 239.3 | 474.7 / 473.9 | 14 of 14 |
| physical cores, ngram-simple drafts | 248.9 / 240.9 | 502.7 / 526.8 | 14 of 14 |
| physical cores, ngram-mod drafts | 248.7 / 244.2 | 486.4 / 487.1 | **2 of 14** |

- **Threads.** On Linux the physical cores were about 5 % faster (they read the prompt faster: 94 to 96 tokens per second against 75 to 78). On Windows, Freewill's main target, they were about 4 % slower (generation fell from 12.2–12.5 to 10.8 tokens per second). **The default does not change.** `FREEWILL_THREADS=physical` asks for the physical cores.
- **Drafts.** ngram-simple kept the answers but saved no time: 111 of 608 drafted tokens accepted on Linux, 64 of 768 on Windows. ngram-mod changed 12 answers of 14 even greedy. **Both stay off.** `FREEWILL_DRAFT=ngram` turns the first on, to try.
- **Prompt cache.** llama-server already reuses what two requests share: 11,338 of 18,840 prompt tokens came from its cache in every configuration. Nothing to add.

## For larger models: colibri as an external engine

colibri serves its models through an OpenAI-compatible address (`http://127.0.0.1:8000/v1`), which Freewill can already use as an engine of kind `compatible`. That is how a computer with 16 to 32 GB could think with a mixture-of-experts model far larger than Qwen3 1.7B. It was not measured with Freewill. A life that thinks with an external engine does not train it at night: only the embedded engine and Freewill 1.8B-V learn.

## Limits

Two runners, one CPU family, no graphics card, no macOS; one run of each Freewill 1.8B-V configuration, two of each llama.cpp configuration. The bridge of Freewill 1.8B-V was untrained (text only), which changes nothing to the speed. Answers to a person in the application are sampled, not greedy: the time is the same, the words are not compared there.
