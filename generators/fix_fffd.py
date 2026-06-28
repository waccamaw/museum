import sys, re
for p in sys.argv[1:]:
    t = open(p, encoding="utf-8").read()
    before = t.count("�")
    # between letters -> apostrophe (I'm, that's, I've, I'd)
    t = re.sub(r"(?<=[A-Za-z])�(?=[A-Za-z])", "’", t)
    # letter then FFFD then space (sucks… , boredom…) -> drop the char
    t = re.sub(r"�", "", t)
    open(p, "w", encoding="utf-8").write(t)
    print(f"{p}: U+FFFD {before} -> {t.count(chr(0xFFFD))}")
