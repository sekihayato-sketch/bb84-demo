import streamlit as st
import random
import pandas as pd
import hashlib

st.set_page_config(page_title="BB84 QKD Simulator", layout="wide")

st.title("BB84量子鍵配送シミュレータ")
st.caption("シフティング → QBER評価 → 誤り訂正 → プライバシー増幅までを体験する教育用アプリ")

st.markdown("""
このアプリでは、BB84プロトコルにおける **基底選択**、**シフティング**、**QBERによる鍵破棄判定**、
簡略化した **誤り訂正** と **プライバシー増幅** を確認できます。

※ 誤り訂正とプライバシー増幅は、インターン説明用の簡略モデルです。実際のQKD装置で使う実装とは異なります。
""")

with st.sidebar:
    st.header("シミュレーション条件")
    num_bits = st.slider("送信ビット数", 8, 256, 32, step=8)
    eve_enabled = st.checkbox("Eveによる盗聴を有効化", value=True)
    eve_rate = st.slider("Eveが介入する割合 [%]", 0, 100, 100, step=5, disabled=not eve_enabled)
    noise_rate = st.slider("通信路ノイズ率 [%]", 0, 20, 0, step=1)
    qber_threshold = st.slider("鍵破棄しきい値 QBER [%]", 0.0, 20.0, 11.0, step=0.5)
    st.caption("教育用として、QBERがこのしきい値以下なら鍵生成処理へ進む設定です。")

bases = ["+", "×"]

basis_label = {
    "+": "＋基底",
    "×": "×基底",
}

def bits_to_string(bits):
    return "".join(str(b) for b in bits) if bits else "-"

def hash_to_bits(text, length):
    if length <= 0:
        return "-"
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    bit_string = "".join(f"{byte:08b}" for byte in digest)
    while len(bit_string) < length:
        digest = hashlib.sha256((bit_string + text).encode("utf-8")).digest()
        bit_string += "".join(f"{byte:08b}" for byte in digest)
    return bit_string[:length]

if st.button("シミュレーション実行", type="primary"):
    alice_bits = [random.randint(0, 1) for _ in range(num_bits)]
    alice_bases = [random.choice(bases) for _ in range(num_bits)]
    bob_bases = [random.choice(bases) for _ in range(num_bits)]

    bob_results = []
    eve_bases = []
    eve_results = []
    eve_intervened = []
    noise_flipped = []

    for i in range(num_bits):
        transmitted_bit = alice_bits[i]
        transmitted_basis = alice_bases[i]

        does_eve_intervene = eve_enabled and random.randint(1, 100) <= eve_rate
        eve_intervened.append("○" if does_eve_intervene else "-")

        if does_eve_intervene:
            eve_basis = random.choice(bases)
            eve_bases.append(eve_basis)

            if eve_basis == alice_bases[i]:
                eve_result = alice_bits[i]
            else:
                eve_result = random.randint(0, 1)

            eve_results.append(eve_result)
            transmitted_bit = eve_result
            transmitted_basis = eve_basis
        else:
            eve_bases.append("-")
            eve_results.append("-")

        if bob_bases[i] == transmitted_basis:
            bob_result = transmitted_bit
        else:
            bob_result = random.randint(0, 1)

        does_noise_flip = random.randint(1, 100) <= noise_rate
        if does_noise_flip:
            bob_result = 1 - bob_result
        noise_flipped.append("○" if does_noise_flip else "-")

        bob_results.append(bob_result)

    same_basis = [alice_bases[i] == bob_bases[i] for i in range(num_bits)]
    used_for_key = same_basis
    key_error = [same_basis[i] and alice_bits[i] != bob_results[i] for i in range(num_bits)]

    alice_key = [alice_bits[i] for i in range(num_bits) if used_for_key[i]]
    bob_key = [bob_results[i] for i in range(num_bits) if used_for_key[i]]

    key_length = len(alice_key)
    errors = sum(1 for a, b in zip(alice_key, bob_key) if a != b)
    qber = errors / key_length * 100 if key_length > 0 else 0.0

    can_generate_key = key_length > 0 and qber <= qber_threshold

    # 簡略化した誤り訂正：説明用に、不一致箇所を検出してBob側をAlice側に合わせるモデル
    if can_generate_key:
        corrected_bob_key = alice_key.copy()
        corrected_errors = 0
        ec_leakage_bits = errors
    else:
        corrected_bob_key = bob_key.copy()
        corrected_errors = errors
        ec_leakage_bits = 0

    # 簡略化したプライバシー増幅：QBERと誤り訂正で漏れた情報量に応じて鍵を短く圧縮するモデル
    if can_generate_key:
        safety_factor = max(0.0, 1.0 - qber / qber_threshold) if qber_threshold > 0 else 0.0
        final_key_length = max(0, int((key_length - ec_leakage_bits) * safety_factor))
        final_key = hash_to_bits(bits_to_string(corrected_bob_key), final_key_length)
    else:
        final_key_length = 0
        final_key = "-"

    st.subheader("1. 全体結果")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("送信ビット数", num_bits)
    col2.metric("基底一致数", key_length)
    col3.metric("誤り数", errors)
    col4.metric("QBER", f"{qber:.2f}%")
    col5.metric("最終鍵長", f"{final_key_length} bit")

    st.write("QBERしきい値に対する現在値")
    progress_value = min(qber / qber_threshold, 1.0) if qber_threshold > 0 else 1.0
    st.progress(progress_value)

    if can_generate_key and final_key_length > 0:
        st.success("QBERがしきい値以下です。誤り訂正とプライバシー増幅を行い、最終鍵を生成できます。")
    elif can_generate_key and final_key_length == 0:
        st.warning("QBERはしきい値以下ですが、プライバシー増幅後の鍵長が0 bitになりました。送信ビット数を増やすか、誤りを減らしてください。")
    else:
        st.error("QBERがしきい値を超えています。安全な鍵生成は行わず、鍵候補を破棄します。")

    st.subheader("2. BB84の処理フロー")
    f1, f2, f3, f4 = st.columns(4)
    f1.info("① 量子送信\n\nAliceがビットと基底をランダムに選んで送信")
    f2.info("② シフティング\n\nAliceとBobの基底が一致した位置だけ鍵候補に採用")
    f3.info("③ QBER評価\n\n鍵候補のAlice/Bob不一致率を計算")
    f4.info("④ EC・PA\n\n誤り訂正後、プライバシー増幅で鍵を短く圧縮")

    st.subheader("3. 鍵の変化")
    k1, k2 = st.columns(2)
    with k1:
        st.markdown("**シフティング後のAlice鍵候補**")
        st.code(bits_to_string(alice_key), language="text")
        st.markdown("**シフティング後のBob鍵候補**")
        st.code(bits_to_string(bob_key), language="text")
    with k2:
        st.markdown("**誤り訂正後のBob鍵候補（簡略モデル）**")
        st.code(bits_to_string(corrected_bob_key), language="text")
        st.markdown("**プライバシー増幅後の最終鍵（簡略モデル）**")
        st.code(final_key, language="text")

    st.subheader("4. 視覚的な内訳")
    summary_df = pd.DataFrame({
        "項目": ["送信ビット", "基底一致", "鍵候補中の誤り", "最終鍵"],
        "bit数": [num_bits, key_length, errors, final_key_length],
    }).set_index("項目")
    st.bar_chart(summary_df)

    st.subheader("5. 送受信結果の詳細")
    df = pd.DataFrame({
        "No.": list(range(1, num_bits + 1)),
        "Alice Bit": alice_bits,
        "Alice Basis": alice_bases,
        "Eve介入": eve_intervened,
        "Eve Basis": eve_bases,
        "Eve Result": eve_results,
        "Bob Basis": bob_bases,
        "Bob Result": bob_results,
        "Noise Flip": noise_flipped,
        "Basis Match": ["○" if x else "×" for x in same_basis],
        "Used for Key": ["○" if x else "×" for x in used_for_key],
        "Key Error": ["○" if x else "-" for x in key_error],
        "意味": [
            "鍵候補だが誤りあり" if key_error[i]
            else "鍵候補" if used_for_key[i]
            else "基底不一致で破棄"
            for i in range(num_bits)
        ],
    })

    def highlight_rows(row):
        if row["Key Error"] == "○":
            return ["background-color: #ffe6e6"] * len(row)
        if row["Used for Key"] == "○":
            return ["background-color: #e8f5e9"] * len(row)
        return ["background-color: #f5f5f5"] * len(row)

    st.dataframe(df.style.apply(highlight_rows, axis=1), use_container_width=True)

    with st.expander("この表の見方"):
        st.markdown("""
        - **Basis Match = ○**：AliceとBobの基底が一致した位置です。シフティングで鍵候補になります。
        - **Used for Key = ○**：シフティング後の鍵候補に採用された位置です。
        - **Key Error = ○**：鍵候補に採用されたが、Alice BitとBob Resultが一致していない位置です。
        - **QBER**：`Key Errorの数 ÷ 基底一致数 × 100` で計算しています。
        - **Eve介入 = ○** でも、直接その行を破棄しているわけではありません。破棄判断はQBERで行います。
        """)
else:
    st.info("左の条件を設定して、［シミュレーション実行］を押してください。")
