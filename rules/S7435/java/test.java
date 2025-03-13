
User user = new User(
    Settings.Secure.getString(mContext.getContentResolver(), Settings.Secure.ANDROID_ID), // Sensitive
    "John",
    "Doe",
)

User user = new User(
    UUID.randomUUID().toString(),
    "John",
    "Doe",
)

