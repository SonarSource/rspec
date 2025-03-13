
val user = User(
    Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID)), // Sensitive
    "John",
    "Doe",
)

val user = new User(
    UUID.randomUUID().toString(),
    "John",
    "Doe",
)
