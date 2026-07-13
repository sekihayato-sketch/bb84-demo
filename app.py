import streamlit as st
import random
import pandas as pd

st.title("BB84量子鍵配送シミュレータ")

st.write("""
このアプリでは、BB84プロトコルにおける
AliceとBobの基底選択、鍵のふるい分け、Eveによる盗聴の影響を体験できます。
""")

num_bits = st.slider("送信ビット数", 8, 128, 32)
eve_enabled = st.checkbox("Eveによる盗聴を有効化")

bases = ["+", "×"]

if st.button("シミュレーション実行"):

    alice_bits = [random.randint(0, 1) for _ in range(num_bits)]
    alice_bases = [random.choice(bases) for _ in range(num_bits)]
    bob_bases = [random.choice(bases) for _ in range(num_bits)]

    bob_results = []
    eve_bases = []
    eve_results = []

    for i in range(num_bits):

        transmitted_bit = alice_bits[i]
        transmitted_basis = alice_bases[i]

        if eve_enabled:
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

        bob_results.append(bob_result)

    same_basis = [
        alice_bases[i] == bob_bases[i]
        for i in range(num_bits)
    ]

    alice_key = [
        alice_bits[i]
        for i in range(num_bits)
        if same_basis[i]
    ]

    bob_key = [
        bob_results[i]
        for i in range(num_bits)
        if same_basis[i]
    ]

    errors = sum(
        1 for a, b in zip(alice_key, bob_key)
        if a != b
    )

    key_length = len(alice_key)

    qber = (
        errors / key_length * 100
        if key_length > 0
        else 0
    )

    df = pd.DataFrame({
        "No.": list(range(1, num_bits + 1)),
        "Alice Bit": alice_bits,
        "Alice Basis": alice_bases,
        "Eve Basis": eve_bases,
        "Eve Result": eve_results,
        "Bob Basis": bob_bases,
        "Bob Result": bob_results,
        "Basis Match": ["○" if x else "×" for x in same_basis],
        "Used for Key": ["○" if x else "×" for x in same_basis],
    })

    st.subheader("送受信結果")
    st.dataframe(df)

    st.subheader("ふるい分け後の鍵")
    st.write("Alice Key:", alice_key)
    st.write("Bob Key:", bob_key)

    st.subheader("結果")
    st.write(f"送信ビット数: {num_bits}")
    st.write(f"基底一致数: {key_length}")
    st.write(f"誤り数: {errors}")
    st.write(f"QBER: {qber:.2f}%")

    if qber > 0:
        st.warning("盗聴またはノイズによる誤りが検出されました。鍵は破棄する判断になります。")
    else:
        st.success("誤りは検出されませんでした。鍵候補として利用できます。")
