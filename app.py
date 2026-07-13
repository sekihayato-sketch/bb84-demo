import streamlit as st
import random
import pandas as pd

st.title("BB84量子鍵配送シミュレータ")

st.write("AliceとBobが鍵を共有し、Eveによる盗聴の影響を確認できます。")

num_bits = st.slider("送信ビット数", 8, 128, 32)
eve_enabled = st.checkbox("Eveによる盗聴を有効化")

bases = ["+", "×"]

if st.button("シミュレーション実行"):

    alice_bits = [random.randint(0, 1) for _ in range(num_bits)]
    alice_bases = [random.choice(bases) for _ in range(num_bits)]
    bob_bases = [random.choice(bases) for _ in range(num_bits)]

    bob_results = []

    for i in range(num_bits):

        transmitted_bit = alice_bits[i]
        transmitted_basis = alice_bases[i]

        if eve_enabled:
            eve_basis = random.choice(bases)

            if eve_basis != alice_basestransmitted_bit = random.randint(0, 1)

            transmitted_basis = eve_basis

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

    qber = (
        errors / len(alice_key) * 100
        if len(alice_key) > 0
        else 0
    )

    df = pd.DataFrame({
        "Alice Bit": alice_bits,
        "Alice Basis": alice_bases,
        "Bob Basis": bob_bases,
        "Bob Result": bob_results,
        "Basis Match": same_basis
    })

    st.subheader("送受信結果")
    st.dataframe(df)

    st.subheader("結果")
    st.write(f"共有鍵長: {len(alice_key)} bit")
    st.write(f"誤り数: {errors}")
    st.write(f"QBER: {qber:.2f}%")

    if qber > 0:
        st.warning("盗聴またはノイズが検出されました")
    else:
        st.success("誤りは検出されませんでした")
