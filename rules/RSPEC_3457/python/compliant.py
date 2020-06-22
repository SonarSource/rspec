"Error %(message)s" % {"message": "something failed"}

"Error: User {} has not been able to access {}".format("Alice", "MyFile")

user = "Alice"
resource = "MyFile"
message = f"Error: User {user} has not been able to access {resource}"

import logging
logging.error("Error: User %s has not been able to access %s", "Alice", "MyFile")