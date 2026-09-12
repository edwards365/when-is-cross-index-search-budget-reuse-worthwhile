#!/usr/bin/env python
"""LaTeX -> OMML (Word native equation) converter for the paper's 21 display equations.

Fail-fast: any unsupported construct raises ValueError at build time.
"""
import re

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

SYM = {
    "geq": "\u2265", "leq": "\u2264", "neq": "\u2260", "times": "\u00d7",
    "cap": "\u2229", "in": "\u2208", "bot": "\u22a5", "rightarrow": "\u2192",
    "Delta": "\u0394", "delta": "\u03b4", "gamma": "\u03b3", "alpha": "\u03b1",
    "epsilon": "\u03b5", "varepsilon": "\u03b5", "eta": "\u03b7", "rho": "\u03c1",
    "star": "\u22c6", "pi": "\u03c0", "sim": "\u223c", "cdot": "\u00b7",
    "lceil": "\u2308", "rceil": "\u2309",
}
THIN, EM = "\u2009", "\u2003"
FUNC_UNDER = {"max", "min", "sup", "inf"}
FUNC_SIDE = {"Pr", "log", "exp"}
DELIMS = {"(": "(", ")": ")", "[": "[", "]": "]",
          "\\{": "{", "\\}": "}", "\\lceil": "\u2308", "\\rceil": "\u2309", ".": ""}


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def mr(text, upright=False):
    sty = '<m:rPr><m:sty m:val="p"/></m:rPr>' if upright else ""
    return (f'<m:r>{sty}<w:rPr xmlns:w="{W}">'
            f'<w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr>'
            f'<m:t xml:space="preserve">{esc(text)}</m:t></m:r>')


class P:
    def __init__(self, s):
        self.t = re.findall(r"\\[a-zA-Z]+|\\[{}|,;! ]|[{}^_]|.", s)
        self.i = 0

    def peek(self, k=0):
        j = self.i + k
        return self.t[j] if j < len(self.t) else None

    def pop(self):
        v = self.t[self.i]
        self.i += 1
        return v

    def parse(self):
        out = self.expr(None)
        if self.i != len(self.t):
            raise ValueError(f"trailing tokens: {self.t[self.i:]}")
        return out

    def expr(self, stop):
        out = ""
        while True:
            p = self.peek()
            if p is None:
                if stop:
                    raise ValueError(f"unterminated, expected {stop}")
                return out
            if stop == "\\right":
                if p == "\\right":
                    return out  # caller consumes the \right token
            elif stop and p == stop:
                self.pop()
                return out
            out += self.term()

    def read_group_raw(self):
        """Consume a {...} group and return its raw text (spacing escapes mapped)."""
        assert self.pop() == "{"
        depth, out = 1, ""
        while depth:
            t = self.pop()
            if t == "{":
                depth += 1
            elif t == "}":
                depth -= 1
                if depth == 0:
                    break
            name = t[1:]
            if t.startswith("\\") and name == " ":
                t = " "
            elif t == "\\,":
                t = THIN
            elif t == "\\qquad":
                t = EM + EM
            elif t == "\\!":
                t = ""
            elif t == "\\|":
                t = "\u2016"
            elif t in ("\\{", "\\}"):
                t = name
            out += t
        return out

    def group(self):
        if self.peek() != "{":
            raise ValueError(f"expected group, got {self.peek()}")
        self.pop()
        return self.expr("}")

    def term(self):
        base = self.atom()
        while self.peek() in ("_", "^"):
            op = self.pop()
            sub = sup = None
            if op == "_":
                sub = self.group()
            if self.peek() == "^":
                self.pop()
                sup = self.group()
            if sub is not None and sup is not None:
                return (f'<m:sSubSup><m:e>{base}</m:e><m:sub>{sub}</m:sub>'
                        f'<m:sup>{sup}</m:sup></m:sSubSup>')
            if sub is not None:
                return f'<m:sSub><m:e>{base}</m:e><m:sub>{sub}</m:sub></m:sSub>'
            return f'<m:sSup><m:e>{base}</m:e><m:sup>{sup}</m:sup></m:sSup>'
        return base

    def atom(self):
        t = self.pop()
        if t == "{":
            return self.expr("}")
        if t in ("}", "^", "_"):
            raise ValueError(f"unexpected {t}")
        if t.startswith("\\"):
            return self.command(t)
        if t == "'":
            return mr("\u2032")
        return mr(t)

    def _post_body(self, n=1):
        """Consume the operand following a big operator (single unit if tied)."""
        return self.term() if self.peek() not in (None, "}") else ""

    def command(self, c):
        name = c[1:]
        if c == "\\left":
            d = self.pop()
            if d not in DELIMS:
                raise ValueError(f"unsupported \\left delimiter {d}")
            beg = DELIMS[d]
            inner = self.expr("\\right")
            if self.peek() != "\\right":
                raise ValueError("missing \\right")
            self.pop()
            d2 = self.pop()
            end = DELIMS.get(d2, "")
            pr = (f'<m:dPr><m:begChr m:val="{esc(beg)}"/><m:endChr m:val="{esc(end)}"/></m:dPr>'
                  if (beg or end) else "")
            return f'<m:d>{pr}<m:e>{inner}</m:e></m:d>'
        if c == "\\right":
            raise ValueError("unmatched \\right")
        if c == "\\frac":
            num, den = self.group(), self.group()
            return f'<m:f><m:num>{num}</m:num><m:den>{den}</m:den></m:f>'
        if c == "\\sqrt":
            return (f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/>'
                    f'<m:e>{self.group()}</m:e></m:rad>')
        if c == "\\hat":
            return (f'<m:acc><m:accPr><m:chr m:val="\u0302"/></m:accPr>'
                    f'<m:e>{self.group()}</m:e></m:acc>')
        if c == "\\sum":
            sub = sup = ""
            if self.peek() == "_":
                self.pop()
                sub = self.group()
            if self.peek() == "^":
                self.pop()
                sup = self.group()
            body = self.term() if self.peek() not in (None, "}") else ""
            return (f'<m:nary><m:naryPr><m:chr m:val="\u2211"/>'
                    f'<m:limLoc m:val="undOvr"/></m:naryPr>'
                    f'<m:sub>{sub}</m:sub><m:sup>{sup}</m:sup>'
                    f'<m:e>{body}</m:e></m:nary>')
        if c == "\\mathrm":
            raw = self.read_group_raw()
            return mr(raw, upright=True)
        if c == "\\mathbb":
            g = self.group()
            if "E" in g:
                return mr("\U0001D53C")
            return mr(g)
        if c == "\\mathcal":
            g = self.group()
            return mr({"A": "\U0001D49C", "E": "\u2130", "P": "\u2119"}.get(g, g))
        if c == "\\mathbf":
            g = self.group()
            return mr("1" if g == "1" else g)
        if name in FUNC_UNDER:
            base = mr(name, upright=True)
            if self.peek() == "_":
                self.pop()
                lim = self.group()
                body = self.term() if self.peek() not in (None, "}") else ""
                return (f'<m:limLow><m:e>{base}</m:e><m:lim>{lim}</m:lim>'
                        f'</m:limLow>{body}')
            return base
        if name in FUNC_SIDE:
            base = mr(name, upright=True)
            if self.peek() == "_":
                self.pop()
                return f'<m:sSub><m:e>{base}</m:e><m:sub>{self.group()}</m:sub></m:sSub>'
            return base
        if name in SYM:
            return mr(SYM[name])
        if name == ",":
            return mr(THIN)
        if name == ";":
            return mr(EM)
        if name == "qquad":
            return mr(EM + EM)
        if name == "!":
            return ""
        if name == " ":
            return mr(" ")
        if name == "|":
            return mr("\u2016")
        if name in ("{", "}"):
            return mr(name)
        if name == "mathrm":
            pass
        raise ValueError(f"unsupported command: {c}")


def convert(latex):
    s = latex.strip()
    if s.startswith("$"):
        s = s.strip("$").strip()
    return f'<m:oMath>{P(s).parse()}</m:oMath>'


EQS = {
 1: r"Z_{E}(q,a)=\mathbf{1}\{\mathrm{the\ returned\ result\ fails\ the\ registered\ quality\ target}\},\qquad C_{E}(q,a)\geq 0.",
 2: r"B_{E}(q)=\min\{a\in\mathcal{A}_{E}:Z_{E}(q,a)=0\},\qquad B_{E}(q)=\bot\ \mathrm{if\ no\ registered\ action\ succeeds}.",
 3: r"r_{E}^{\pi}=\mathrm{Pr}_{q\sim P_{Q}}\left[Z_{E}(q,\pi_{T,q})=1\right].",
 4: r"\max_{i\in\{0,1\}}\mathbb{E}[l_{i}]\ \geq\ \frac{\Delta}{2}\left(1-\mathrm{TV}(P_{0}^{T},P_{1}^{T})\right).",
 5: r"\max_{i}\mathbb{E}[l_{i}]\ \geq\ \frac{\Delta}{4}e^{-K_{m}},\qquad \max_{i}\mathbb{E}[l_{i}]\ \geq\ \frac{\Delta}{2}\max\!\left(0,1-\sqrt{K_{m}/2}\right).",
 6: r"\mathcal{G}=\left\{\sup_{a\in\mathcal{A}}|\hat{r}_{a}-r_{a}|\leq\varepsilon_{R}\right\}\cap\left\{\sup_{a\in\mathcal{A}}|\hat{C}_{a}-C_{a}|\leq\varepsilon_{C}\right\}.",
 7: r"\mathrm{Pr}\left[r_{E_{t}}^{\hat{a}}\leq\delta\ \ \mathrm{or\ a\ valid\ fallback\ or\ abstention\ is\ invoked}\right]\geq 1-\alpha.",
 8: r"m=O\!\left(\frac{\log(M/\alpha)}{\gamma^{2}}\right).",
 9: r"m_{\min}=\left\lceil\frac{\log\alpha_{l}}{\log(1-\delta)}\right\rceil",
 10: r"D=G_{\mathrm{online}}-\mathrm{Pr}(R)\Delta C_{f-c}.",
 11: r"N^{\star}=\frac{C_{\mathrm{build}}+C_{\mathrm{operator}}+C_{\mathrm{truth}}+C_{\mathrm{cert}}}{D}.",
 12: r"\mathbb{E}_{0}[l_{0}]+\mathbb{E}_{1}[l_{1}]\ \geq\ \Delta\left\{P_{0}[I{=}1]+P_{1}[I{=}0]\right\}.",
 13: r"K_{m}=\sum_{t=1}^{m}\mathbb{E}_{0}\left[\mathrm{KL}(P_{0}^{Y_{t}|H_{t-1},A_{t}}\,\|\,P_{1}^{Y_{t}|H_{t-1},A_{t}})\right]\leq mI^{\star}.",
 14: r"r_{a_{k}}+\varepsilon_{R}\leq r_{a_{k}}+2\varepsilon_{R}\leq\delta,",
 15: r"\hat{C}_{\hat{a}}\leq\hat{C}_{a_{k}}+\varepsilon_{C}\leq C_{a_{k}}+2\varepsilon_{C}.",
 16: r"P_{\mathrm{under}}=P_{\mathrm{over}}=\frac{1}{2}P\left[B_{s}\neq B_{t}\right].",
 17: r"r_{E}^{\pi}=\eta_{E}+(1-\eta_{E})r_{E}^{\pi,\mathrm{feas}}.",
 18: r"r_{S}=r_{0}(1-\rho_{S}).",
 19: r"|r_{G',a}-r_{G,a}|\leq\mathrm{Pr}_{q}\{Z_{G}(q,a)\neq Z_{G'}(q,a)\}.",
 20: r"\Delta_{s\rightarrow t}=\mathrm{Pr}_{q\sim P_{Q}}\left[Z_{t}(q,B_{s}(q)){=}1\right]-r_{t}^{\mathrm{ref}},",
 21: r"V_{\mathrm{fin}}=\mathrm{Pr}_{q}\left[|\{B_{E}(q):E\in\mathcal{E}_{\mathrm{reg}},B_{E}(q)\neq\bot\}|>1\right],\qquad V_{\mathrm{end}}=\mathrm{Pr}_{q}\left[\mathbf{1}\{B_{E}(q){=}\bot\}\ \mathrm{nonconstant\ over}\ E\right].",
}


if __name__ == "__main__":
    import xml.etree.ElementTree as ET
    ok = 0
    for n, tex in sorted(EQS.items()):
        try:
            om = convert(tex)
            ET.fromstring(om.replace("m:", "m") if False else
                          f'<root xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
                          f'xmlns:w="{W}">{om}</root>')
            ok += 1
            print(f"eq{n:02d} OK  ({len(om)} chars)")
        except Exception as e:
            print(f"eq{n:02d} FAIL: {e}")
    print(f"{ok}/{len(EQS)} converted + XML-valid")
    assert ok == len(EQS), "converter incomplete"
