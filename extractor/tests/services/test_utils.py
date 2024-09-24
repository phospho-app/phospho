from extractor.utils import fits_in_context_window


def test_fits_in_context_window():
    prompt = "tiktoken is great!"
    context_window_size = 100

    assert fits_in_context_window(prompt, context_window_size) is True

    prompt = "tiktoken is great!"
    context_window_size = 1

    assert fits_in_context_window(prompt, context_window_size) is False
