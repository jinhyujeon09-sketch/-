import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="자동 채점기", page_icon="📝", layout="centered")
st.title("📝 자동 채점기")

CIRCLED = {1: "①", 2: "②", 3: "③", 4: "④", 5: "⑤"}


# ---------------------------------------------------------------- 정답 설정
with st.sidebar:
    st.header("정답 설정")
    n = st.number_input("문항 수", min_value=1, max_value=100, value=5, step=1)
    tol = st.number_input("주관식 허용 오차", min_value=0.0, value=0.0, step=0.01,
                          help="0이면 정확히 같아야 정답. 예: 0.05면 ±0.05까지 정답")
    st.caption("문항별 유형과 정답을 입력하세요.")

    key = {}
    for i in range(1, n + 1):
        c1, c2 = st.columns([1, 1])
        t = c1.selectbox(f"{i}번 유형", ["객관식", "주관식"], key=f"type_{i}")
        if t == "객관식":
            a = c2.selectbox("정답", [1, 2, 3, 4, 5], key=f"key_{i}",
                             format_func=lambda x: CIRCLED[x])
        else:
            a = c2.number_input("정답", key=f"key_{i}", value=0.0, format="%g")
        key[i] = (t, a)


# ---------------------------------------------------------------- 빠른 입력
def apply_quick():
    """'1.4번 2.9' 같은 문자열을 파싱해서 입력칸에 채워 넣는다."""
    text = st.session_state.get("quick", "")
    for q, val in re.findall(r"(\d+)\s*[.)]\s*(-?\d+(?:\.\d+)?)\s*번?", text):
        q = int(q)
        if q not in key:
            continue
        if key[q][0] == "객관식":
            try:
                v = int(float(val))
            except ValueError:
                continue
            if 1 <= v <= 5:
                st.session_state[f"ans_{q}"] = v
        else:
            st.session_state[f"ans_{q}"] = val


with st.expander("⚡ 한 번에 붙여넣기 (예: 1.4번 2.9 3.2번)"):
    st.caption("형식은 `문항번호.답` 입니다. 객관식은 뒤에 '번', 주관식은 숫자만.")
    st.text_input("답 문자열", key="quick", placeholder="1.4번 2.9 3.2번")
    st.button("입력칸에 적용", on_click=apply_quick)


# ---------------------------------------------------------------- 답안 입력
st.subheader("답안 입력")
answers = {}
for i in range(1, n + 1):
    t, _ = key[i]
    if t == "객관식":
        answers[i] = st.radio(
            f"{i}번", [1, 2, 3, 4, 5], index=None, horizontal=True,
            format_func=lambda x: CIRCLED[x], key=f"ans_{i}",
        )
    else:
        answers[i] = st.text_input(f"{i}번 (주관식)", key=f"ans_{i}",
                                   placeholder="숫자를 입력하세요")


# ---------------------------------------------------------------- 채점
def is_correct(t, correct, given):
    if given is None or str(given).strip() == "":
        return False
    if t == "객관식":
        return int(given) == int(correct)
    try:
        return abs(float(str(given).strip()) - float(correct)) <= tol + 1e-9
    except ValueError:
        return False


if st.button("채점하기", type="primary"):
    rows, score = [], 0
    for i in range(1, n + 1):
        t, correct = key[i]
        given = answers[i]
        ok = is_correct(t, correct, given)
        score += ok
        rows.append({
            "문항": i,
            "유형": t,
            "내 답": "-" if given in (None, "") else (CIRCLED[given] if t == "객관식" else given),
            "정답": CIRCLED[correct] if t == "객관식" else f"{correct:g}",
            "결과": "⭕" if ok else "❌",
        })
    st.success(f"점수: {score} / {n}  ({score / n * 100:.0f}점)")
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
