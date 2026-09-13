"""
EPİAŞ GÖP PTF Tahmin & Trading Terminali — Kimlik Doğrulama & Erişim Ağ Geçidi
Sıfır emoji politikası ve kurumsal koyu terminal tasarımına uygun oturum yönetimi.
"""

import os
from datetime import datetime
import streamlit as st


def get_configured_access_keys() -> list[str]:
    """
    Sisteme giriş için geçerli erişim anahtarlarını döndürür.
    Sırasıyla st.secrets, os.environ veya varsayılan kurumsal anahtarları kontrol eder.
    """
    valid_keys = set()
    
    # 1. Streamlit Cloud secrets kontrolü
    try:
        if hasattr(st, "secrets") and "TERMINAL_ACCESS_KEY" in st.secrets:
            secret_val = st.secrets["TERMINAL_ACCESS_KEY"]
            if isinstance(secret_val, list):
                valid_keys.update(secret_val)
            else:
                valid_keys.add(str(secret_val))
    except Exception:
        pass

    # 2. Ortam değişkeni kontrolü
    env_key = os.getenv("TERMINAL_ACCESS_KEY")
    if env_key:
        valid_keys.add(env_key)

    # 3. Varsayılan kurumsal demo anahtarları
    valid_keys.update(["epias2026", "admin2026", "trader2026"])
    
    return [k.strip() for k in valid_keys if k.strip()]


def require_terminal_auth() -> bool:
    """
    Kullanıcının terminale erişim yetkisi olup olmadığını denetler.
    Yetkisiz ise şık bir kurumsal giriş ekranı gösterir ve st.stop() çağırır.
    Yetkili ise True döndürerek uygulamanın çalışmasını sürdürür.
    """
    if st.session_state.get("authenticated", False):
        return True

    # Giriş ekranında yan paneli gizle
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    valid_keys = get_configured_access_keys()

    col_l, col_center, col_r = st.columns([1, 1.8, 1])
    with col_center:
        st.markdown("<div style='height: 48px;'></div>", unsafe_allow_html=True)
        
        st.markdown(
            """
            <div style="
                background: linear-gradient(180deg, #141a26 0%, #0c1017 100%);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 12px;
                padding: 32px 36px 28px 36px;
                box-shadow: 0 20px 50px rgba(0,0,0,0.6);
                text-align: center;
                font-family: 'Inter', -apple-system, sans-serif;
            ">
                <div style="font-size: 0.72rem; color: #60a5fa; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 6px;">
                    [GÜVENLİK PROTOKOLÜ: DÜZEY-2]
                </div>
                <div style="font-size: 1.45rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.02em; margin-bottom: 6px;">
                    EPİAŞ GÖP TAHMİN & TRADING TERMİNALİ
                </div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-bottom: 24px;">
                    Kurumsal Enerji Masası Karar Destek Arayüzü
                </div>
                <div style="border-top: 1px solid rgba(255,255,255,0.06); margin-bottom: 24px;"></div>
                <div style="text-align: left; font-size: 0.75rem; color: #cbd5e1; font-family: 'JetBrains Mono', monospace; margin-bottom: 8px;">
                    TERMİNAL ERİŞİM ANAHTARI (ACCESS KEY):
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Form alanı
        with st.form("terminal_login_form", clear_on_submit=False):
            entered_key = st.text_input(
                "Erişim Anahtarı",
                type="password",
                placeholder="Erişim anahtarınızı giriniz...",
                label_visibility="collapsed",
            )
            
            submit_btn = st.form_submit_button(
                "Terminale Bağlan (Login)",
                use_container_width=True,
            )

        if submit_btn:
            if entered_key and entered_key.strip() in valid_keys:
                st.session_state["authenticated"] = True
                st.session_state["auth_user"] = "TRADER-01 (Kıdemli Portföy Yöneticisi)"
                st.session_state["login_time"] = datetime.now().strftime("%H:%M:%S")
                st.rerun()
            else:
                st.error("[ERİŞİM REDDEDİLDİ] Girilen erişim anahtarı geçersiz veya yetkisiz.")

        # Demo ipucu kartı
        st.markdown(
            """
            <div style="
                margin-top: 16px;
                background: rgba(15, 23, 42, 0.6);
                border: 1px dashed rgba(255,255,255,0.1);
                border-radius: 8px;
                padding: 12px 16px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.72rem;
                color: #64748b;
                text-align: center;
            ">
                <span style="color: #94a3b8; font-weight: 600;">Staj / Değerlendirme Demo Anahtarı:</span> 
                <span style="color: #38bdf8; font-weight: 700;">epias2026</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.stop()


def render_sidebar_user_badge():
    """Giriş yapmış kullanıcının durumunu ve çıkış butonunu sol panelin en üstünde gösterir."""
    if not st.session_state.get("authenticated", False):
        return

    user_name = st.session_state.get("auth_user", "TRADER-01")
    login_time = st.session_state.get("login_time", "--:--:--")

    with st.sidebar:
        st.markdown(
            f"""
            <div style="
                background: rgba(30, 41, 59, 0.4);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 8px;
                padding: 10px 14px;
                margin-bottom: 12px;
                font-family: 'JetBrains Mono', monospace;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <span style="font-size: 0.65rem; color: #22c55e; font-weight: 700; letter-spacing: 0.05em;">[OTURUM AKTİF]</span>
                    <span style="font-size: 0.65rem; color: #64748b;">TSI {login_time}</span>
                </div>
                <div style="font-size: 0.76rem; font-weight: 600; color: #f1f5f9;">
                    {user_name}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Güvenli Çıkış Yap (Logout)", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state.pop("auth_user", None)
            st.session_state.pop("login_time", None)
            st.rerun()
