#include <stdio.h>

int main() {
    printf("%d", 1, 2); // Noncompliant; the second argument "2" is unused
    printf("%0-f", 1.2); // Noncompliant; flag "0" is ignored because of "-"
}