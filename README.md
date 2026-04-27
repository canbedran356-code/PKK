# 🤖 Telegram Grup Yönetim Botu

Railway üzerinde çalışan, tam özellikli bir Telegram grup yönetim botu.

## ✨ Özellikler

| Komut | Açıklama |
|-------|----------|
| `/ban` | Kullanıcıyı gruptan banlar |
| `/unban` | Kullanıcının banını kaldırır |
| `/warn` | Kullanıcıya uyarı verir (3 uyarı = otomatik ban) |
| `/unwarn` | Kullanıcının bir uyarısını siler |
| `/warns` | Kullanıcının uyarı sayısını gösterir |
| `/mute` | Kullanıcıyı susturur |
| `/unmute` | Kullanıcının sesini açar |
| 👋 Hoşgeldin | Gruba katılınca otomatik mesaj |
| 😢 Gülegüle | Gruptan ayrılınca otomatik mesaj |

## 🚀 Railway'de Kurulum

### 1. Bot Token Al
1. Telegram'da [@BotFather](https://t.me/BotFather) ile konuş
2. `/newbot` yaz ve talimatları takip et
3. Sana verilen **token**'ı kopyala

### 2. BotFather Ayarları
BotFather'da botuna şu ayarı yap:
- `/setprivacy` → Bot'unu seç → `Disable` (grup mesajlarını görmesi için)

### 3. Railway'e Deploy Et
1. [railway.app](https://railway.app) hesabı oluştur
2. **New Project** → **Deploy from GitHub repo**
3. Bu klasörü bir GitHub repo'suna yükle
4. Railway'de projeyi seç

### 4. Ortam Değişkeni Ekle
Railway dashboard'unda:
- **Variables** sekmesine git
- Şunu ekle:
  ```
  BOT_TOKEN = 123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
  ```

### 5. Botu Gruba Ekle
1. Botu grubuna admin olarak ekle
2. Şu izinleri ver:
   - ✅ Üyeleri yasakla
   - ✅ Mesajları sil
   - ✅ Üyeleri kısıtla

## 📋 Komut Kullanımı

Tüm komutlar **reply** veya **kullanıcı ID'si** ile çalışır:

```
# Reply ile:
[mesaja reply at] → /ban Kural ihlali

# ID ile:
/ban 123456789 Spam yaptı
/warn 123456789
/mute 123456789
```

## ⚙️ Yapılandırma

`bot.py` dosyasında `WARN_LIMIT` değişkenini değiştirerek kaç uyarıda ban atılacağını ayarlayabilirsin (varsayılan: 3).

```python
WARN_LIMIT = 3  # Kaç uyarıda ban atılacak
```

## 📦 Gereksinimler

- Python 3.10+
- python-telegram-bot==21.6
