import discord
from discord.ext import commands
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime
import streamlit as st

st.set_page_config(page_title="My App", layout="centered")

st.title("🚀 Welcome to My Streamlit App")

st.markdown("""
This is a simple Streamlit application.

You can use this space to:
- Explain what your project does
- Give instructions to users
- Add context or documentation

Feel free to customize this text however you like.
""")

st.header("📌 About")
st.write("This app is designed to help with data analysis and column matching.")

st.header("🛠️ Instructions")
st.write("Upload your files and adjust the settings to begin.")

# ===============================
# GOOGLE SHEETS SETUP
# ===============================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

#creds = Credentials.from_service_account_file(
#    "streamlit-stock-f9c40bf2de1b.json",
#    scopes=SCOPES
#)
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPES
)

client_gs = gspread.authorize(creds)
sheet = client_gs.open("Bot_gastos").sheet1

# ===============================
# DISCORD BOT SETUP
# ===============================
DISCORD_TOKEN = st.secrets["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===============================
# COMMAND: !gasto (rápido)
# ===============================
@bot.command(name="gasto")
async def add_expense(ctx, *, data):
    """
    Nuevo Formato (sin total):
    !gasto Producto, CostoUnidad, Unidades, Fecha(YYYY-MM-DD), Empresa, Lugar
    """

    try:
        parts = [p.strip() for p in data.split(",")]

        if len(parts) != 6:
            return await ctx.send(
                "❌ Formato incorrecto.\n"
                "Usa:\n`!gasto Producto, CostoUnidad, Unidades, Fecha(YYYY-MM-DD), Empresa, Lugar`"
            )

        producto = parts[0]
        costo_unidad = float(parts[1])
        unidades = int(parts[2])
        fecha_pago = parts[3]
        empresa = parts[4]
        lugar = parts[5]

        # Validar fecha
        try:
            datetime.strptime(fecha_pago, "%Y-%m-%d")
        except:
            return await ctx.send("❌ Fecha inválida. Usa formato YYYY-MM-DD.")

        # Calcular total
        total = costo_unidad * unidades

        # Append row to Google Sheet
        row = [
            producto,
            costo_unidad,
            unidades,
            total,
            fecha_pago,
            empresa,
            lugar
        ]

        sheet.append_row(row)

        await ctx.send(
            f"✅ Gasto agregado:\n"
            f"**{producto}** — {unidades} x ${costo_unidad} = **${total}**"
        )

    except Exception as e:
        await ctx.send(f"⚠️ Error: `{str(e)}`")


# ================================================
# NEW COMMAND: !gasto_ask (modo interactivo)
# ================================================
@bot.command(name="gasto_ask")
async def gasto_ask(ctx):

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    await ctx.send("📝 **Vamos a registrar un gasto.**\nEscribe el **producto**:")
    producto_msg = await bot.wait_for("message", check=check)
    producto = producto_msg.content.strip()

    await ctx.send("💵 ¿Costo por unidad?")
    costo_msg = await bot.wait_for("message", check=check)
    try:
        costo_unidad = float(costo_msg.content.strip())
    except:
        return await ctx.send("❌ Costo inválido. Cancelo el proceso.")

    await ctx.send("📦 ¿Cuántas unidades?")
    unidades_msg = await bot.wait_for("message", check=check)
    try:
        unidades = int(unidades_msg.content.strip())
    except:
        return await ctx.send("❌ Unidades inválidas. Cancelo el proceso.")

    await ctx.send("📅 ¿Fecha de pago? (YYYY-MM-DD)")
    fecha_msg = await bot.wait_for("message", check=check)
    fecha_pago = fecha_msg.content.strip()
    try:
        datetime.strptime(fecha_pago, "%Y-%m-%d")
    except:
        return await ctx.send("❌ Fecha inválida. Cancelo el proceso.")

    await ctx.send("🏪 ¿Empresa/Tienda?")
    empresa_msg = await bot.wait_for("message", check=check)
    empresa = empresa_msg.content.strip()

    await ctx.send("📍 ¿Lugar?")
    lugar_msg = await bot.wait_for("message", check=check)
    lugar = lugar_msg.content.strip()

    # Calcular total automático
    total = costo_unidad * unidades

    # Guardar en la hoja
    row = [
        producto,
        costo_unidad,
        unidades,
        total,
        fecha_pago,
        empresa,
        lugar
    ]
    sheet.append_row(row)

    await ctx.send(
        f"✅ **Gasto guardado exitosamente**\n"
        f"**{producto}** — {unidades} × ${costo_unidad} = **${total}**"
    )


# ===============================
# START BOT
# ===============================
#bot.run(DISCORD_TOKEN)