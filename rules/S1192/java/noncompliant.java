public class Main {
    // tag::include[]
    public void run() {
        prepare("action1"); // Noncompliant - "action1" is duplicated 3 times
        execute("action1");
        release("action1");
    }

    @SuppressWarning("all") // Compliant - annotations are excluded
    private void method1() { /* ... */ }

    @SuppressWarning("all")
    private void method2() { /* ... */ }

    public String method3(String a) {
        System.out.println("'" + a + "'"); // Compliant - literal "'" has less than 5 characters and is excluded
        return ""; // Compliant - literal "" has less than 5 characters and is excluded
    }
    // end::include[]
}