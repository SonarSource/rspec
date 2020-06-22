"Error %(message)s" % {"message": "something failed", "extra": "some dead code"}  # Noncompliant. Remove the unused argument "extra" or add a replacement field.

"Error: User {} has not been able to access []".format("Alice", "MyFile")  # Noncompliant. Remove 1 unexpected argument or add a replacement field.

user = "Alice"
resource = "MyFile"
message = f"Error: User [user] has not been able to access [resource]"  # Noncompliant. Add replacement fields or use a normal string instead of an f-string.

import logging
logging.error("Error: User %s has not been able to access %s", "Alice")  # Noncompliant. Add 1 missing argument.