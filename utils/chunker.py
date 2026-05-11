def chunk_text(
    text,
    chunk_words=250,
    overlap_words=30
):

    if overlap_words >= chunk_words:

        raise ValueError(
            "overlap_words must be smaller than chunk_words"
        )

    words = text.split()

    if len(words) <= chunk_words:
        return [text]

    chunks = []

    step = chunk_words - overlap_words

    for i in range(0, len(words), step):

        end = min(

            i + chunk_words,

            len(words)
        )

        chunk = " ".join(words[i:end])

        chunks.append(chunk)

        if end >= len(words):
            break

    return chunks