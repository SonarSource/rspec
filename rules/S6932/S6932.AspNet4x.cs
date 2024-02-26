using System.Linq;
using System.Net.Http;
using System.Web;
using System.Web.Http;
using System.Web.Mvc;

// Hints: 
// * ApiController: does not expose QueryString or Form directly. The rule does not apply there. See MyApiController test case for details.
// * ControllerBase: does not support model binding, so the rule doesn't applies.
public class TestController : Controller
{
    public ActionResult Post()
    {
        _ = Request.Form["id"]; // Noncompliant {{Use model binding instead of accessing the raw request data}}
        //          ^^^^
        _ = Request.Form.Get("id"); // Noncompliant {{Use model binding instead of accessing the raw request data}}
        //          ^^^^
        _ = Request.Form.GetValues("id"); // Noncompliant {{Use model binding instead of accessing the raw request data}}
        //          ^^^^
        _ = Request.QueryString["id"]; // Noncompliant {{Use model binding instead of accessing the raw request data}}
        //          ^^^^^^^^^^^
        _ = Request.QueryString.Get("id"); // Noncompliant {{Use model binding instead of accessing the raw request data}}
        //          ^^^^^^^^^^^
        _ = Request.QueryString.GetValues("id"); // Noncompliant {{Use model binding instead of accessing the raw request data}}
        //          ^^^^^^^^^^^
        return default;
    }

    // Parameterized for "Form", "QueryString"
    void NoncompliantKeyVariations()
    {
        _ = Request.Form[@"key"]; // Noncompliant
        _ = Request.Form.Get(@"key"); // Noncompliant
        _ = Request.Form.GetValues(@"key"); // Noncompliant

        const string key = "id";
        _ = Request.Form[key]; // Noncompliant
        _ = Request.Form.Get(key); // Noncompliant
        _ = Request.Form.GetValues(key); // Noncompliant
        _ = Request.Form[$"prefix.{key}"]; // Noncompliant
        _ = Request.Form.Get($"prefix.{key}"); // Noncompliant
        _ = Request.Form.GetValues($"prefix.{key}"); // Noncompliant

        _ = Request.Form[name: "id"]; // Noncompliant
        _ = Request.Form.Get(name: "id"); // Noncompliant
        _ = Request.Form.GetValues(name: "id"); // Noncompliant
    }

    // Parameterized: "Form" and "QueryString" and
    void Compliant(string key)
    {
        // Compliant: Accessing by index is not supported by model binding
        _ = Request.Form[0];
        _ = Request.Form.Get(0);
        _ = Request.Form.GetValues(0);
        // Compliant: key is not a compile time constant
        _ = Request.Form[key];
        _ = Request.Form.Get(key);
        _ = Request.Form.GetValues(key);

        _ = Request.Form.AllKeys;
        _ = Request.Form.Count;
        _ = Request.Form.Keys;
        _ = Request.Form.HasKeys();
        _ = Request.Form.GetKey(0);
        Request.Form.Set("id", "value");
        Request.Form.Add("id", "value");
        Request.Form.Remove("id");
    }

    // parameterized test: parameters are the different forbidden Request accesses (see above)
    private static void HandleRequest(HttpRequest request)
    {
        _ = request.Form["id"]; // Noncompliant: Containing type is a controller
        void LocalFunction()
        {
            _ = request.Form["id"]; // Noncompliant: Containing type is a controller
        }
    }
}

// parameterized test: Repeat for Controller, MyBaseController, MyBaseBaseController base classes
public class MyBaseController : Controller { }

public class MyBaseBaseController : MyBaseController { }

public class MyTestController : MyBaseBaseController
{
    public void Action()
    {
        _ = Request.Form["id"]; // Noncompliant
    }
}

static class HttpRequestExtensions
{
    // parameterized test: parameters are the different forbidden Request accesses (see above)
    public static void Ext(this HttpRequest request)
    {
        _ = request.Form["id"]; // Compliant: Not in a controller
    }
}

class RequestService
{
    public HttpRequest Request { get; }

    // parameterized test: parameters are the different forbidden Request accesses (see above)
    public void HandleRequest(HttpRequest request)
    {
        _ = Request.Form["id"]; // Compliant: Not in a controller
    }
}

public class MyApiController : ApiController
{
    public void Action()
    {
        // this.Request.Form["key"] does not compile: Form is not defined.
        // this.Request.QueryString["key"] does not compile: QueryString is not defined.
        this.Request.GetQueryNameValuePairs(); // Compliant: Accesses the whole query at once for e.g. iteration and lookup.
        _ = this.Request.GetQueryNameValuePairs().ToDictionary(kvp => kvp.Key, kvp => kvp.Value)["key"]; // FN: Too complicated to detect.
    }
}