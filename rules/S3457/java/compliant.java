// TODO: Add includes

public class Main
{
    public void main() {
        // tag::String.format[]
        String.format("First %s and then %s", "foo", "bar");
        String.format("Display %2$d and then %d", 1, 3);
        String.format("Too many arguments %d %d", 1, 2);
        String.format("First Line%n");
        String.format("Is myObject null ? %b", myObject == null);
        String.format("value is %d", value);
        String s = "string without arguments";
        // end::String.format[]

        // tag::MessageFormat[]
        MessageFormat.format("Result {0}.", value);
        MessageFormat.format("Result '{0}'  =  {0}", value);
        MessageFormat.format("Result {0}.", myObject);
        // end::MessageFormat[]

        // tag::java.util.Logger[]
        java.util.Logger logger;
        logger.log(java.util.logging.Level.SEVERE, "Result {0}.", myObject);
        logger.log(java.util.logging.Level.SEVERE, "Result {0}'", 14);
        logger.log(java.util.logging.Level.SEVERE, exception, () -> "Result " + param);
        // end::java.util.Logger[]

        // tag::org.slf4j.Logger[]
        org.slf4j.Logger slf4jLog;
        org.slf4j.Marker marker;
        slf4jLog.debug(marker, "message {}");
        slf4jLog.debug(marker, "message {}", 1);
        // end::org.slf4j.Logger[]

        // tag::org.apache.logging.log4j.Logger[]
        org.apache.logging.log4j.Logger log4jLog;
        log4jLog.debug("message {}", 1);
        // end::org.apache.logging.log4j.Logger[]
    }
}
