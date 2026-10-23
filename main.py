import re
import pandas as pd
import streamlit as st

CIRCLED = {1: "①", 2: "②", 3: "③", 4: "④", 5: "⑤"}
TOKEN_SPLIT = re.compile(r"[\s,;]+")


def parse_key(text):
    """정답지 문자열을 '보낸 정답 하나 = 문항 하나'로 변환한다.

    - 공백/쉼표로 구분된 토큰 하나가 정답 하나
    - 뒤에 '번'이 붙으면 객관식(1~5), 숫자만 있으면 주관식
    - '1.4번 2.9'처럼 '문항번호.답' 형식도, '4번 2.9'처럼 답만 나열한 형식도 가능
    반환: (items, errors)  items = [(표시번호, 유형, 정답), ...]
    """
    tokens = [t for t in TOKEN_SPLIT.split(text.strip()) if t]
    numbered = any(re.fullmatch(r"\d+[.)]\d+번", t) for t in tokens)

    items, errors = [], []
    for pos, tok in enumerate(tokens, 1):
        label, body = pos, tok
        if numbered:
            m = re.fullmatch(r"(\d+)[.)](.+)", tok)
            if m:
                label, body = int(m.group(1)), m.group(2)

        if body.endswith("번"):
            num = body[:-1]
            if re.fullmatch(r"\d+", num) and 1 <= int(num) <= 5:
                items.append((label, "객관식", int(num)))
            else:
                errors.append(f"'{tok}' → 객관식 정답은 1~5번만 가능해요")
        else:
            try:
                items.append((label, "주관식", float(body)))
            except ValueError:
                errors.append(f"'{tok}' → 인식하지 못했어요")
    return items, errors


def main():
    st.set_page_config(page_title="자동 채점기", page_icon="📝", layout="centered")
    st.title("📝 자동 채점기")

    # -------------------------------------------------------- 1. 정답지 입력
    st.header("1. 정답지 입력")
    st.caption("객관식은 뒤에 '번', 주관식은 숫자만. 예) 1.4번 2.9 3.2번  또는  4번 2.9 2번")
    key_text = st.text_area("정답", key="key_text", placeholder="1.4번 2.9 3.2번", height=80)
    items, errors = parse_key(key_text)

    for e in errors:
        st.warning(e)
    if not items:
        st.info("정답을 입력하면 다음 단계가 나타나요.")
        st.stop()

    n_mc = sum(1 for _, t, _ in items if t == "객관식")
    st.success(f"정답 {len(items)}개 인식 (객관식 {n_mc}, 주관식 {len(items) - n_mc})")
    with st.expander("인식된 정답 확인"):
        st.dataframe(
            pd.DataFrame([
                {"문항": lb, "유형": t, "정답": CIRCLED[a] if t == "객관식" else f"{a:g}"}
                for lb, t, a in items
            ]),
            hide_index=True, use_container_width=True,
        )

    # -------------------------------------------------------- 2. 내 답 입력
    st.header("2. 내 답 입력")
    st.caption(f"정답 {len(items)}개에 맞춰 입력칸 {len(items)}개가 만들어졌어요.")
    answers = []
    for pos, (lb, t, _) in enumerate(items, 1):
        if t == "객관식":
            answers.append(st.radio(
                f"{lb}번", [1, 2, 3, 4, 5], index=None, horizontal=True,
                format_func=lambda x: CIRCLED[x], key=f"ans_{pos}_mc",
            ))
        else:
            answers.append(st.text_input(
                f"{lb}번 (주관식)", key=f"ans_{pos}_sub", placeholder="숫자를 입력하세요"
            ))

    # -------------------------------------------------------- 3. 채점
    st.header("3. 채점")
    def is_correct(t, correct, given):
        if given is None or str(given).strip() == "":
            return False
        if t == "객관식":
            return int(given) == int(correct)
        try:
            return abs(float(str(given).strip()) - float(correct)) < 1e-9
        except ValueError:
            return False

    if st.button("채점하기", type="primary"):
        rows, score = [], 0
        for (lb, t, correct), given in zip(items, answers):
            ok = is_correct(t, correct, given)
            score += ok
            rows.append({
                "문항": lb,
                "내 답": "-" if given in (None, "") else (CIRCLED[given] if t == "객관식" else given),
                "결과": "⭕" if ok else "❌",
            })
        total = len(items)
        st.success(f"점수: {score} / {total}  ({score / total * 100:.0f}점)")
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


main()
