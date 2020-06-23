public class Main {
    // tag::include[]
    private static final String ACTION_1 = "action1"; // Compliant

    public void run() {
        prepare(ACTION_1); // Compliant
        execute(ACTION_1);
        release(ACTION_1);
    }
    // end::include[]
}