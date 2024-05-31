using System;
using System.Collections.Specialized;
using System.Linq;
using System.Net.Http;
using System.Web;
using System.Web.Http;
using System.Web.Mvc;
using System.Web.Mvc.Filters;
using System.Web.Routing;

// Hints: 
// * ApiController: does not expose QueryString or Form directly. The rule does not apply there. See MyApiController test case for details.
// * ControllerBase: does not support model binding, so the rule doesn't applies.
public class TestController : Controller
{
    private readonly string Key = "id";
    public ActionResult Post()
    {
        _ = Request.Form["id"]; // Noncompliant {{Use model binding instead of accessing the raw request data}}
        //          ^^^^
        _ = Request.Form.Get("id"); // Noncompliant
        //          ^^^^
        _ = Request.Form.GetValues("id"); // Noncompliant
        //          ^^^^
        _ = Request.QueryString["id"]; // Noncompliant {{Use model binding instead of accessing the raw request data}}
        //          ^^^^^^^^^^^
        _ = Request.QueryString.Get("id"); // Noncompliant
        //          ^^^^^^^^^^^
        _ = Request.QueryString.GetValues("id"); // Noncompliant
        //          ^^^^^^^^^^^
        return default;
    }

    // Parameterized for "Form", "QueryString"
    void NoncompliantKeyVariations()
    {
        _ = Request.Form[@"key"]; // Noncompliant
        _ = Request.Form.Get(@"key"); // Noncompliant
        _ = Request.Form.GetValues(@"key"); // Noncompliant

        _ = Request.Form[Key]; // FN: Key is a readonly field with a constant initializer (Requires cross procedure SE)
        const string key = "id";
        _ = Request.Form[key]; // Noncompliant
        _ = Request.Form.Get(key); // Noncompliant
        _ = Request.Form.GetValues(key); // Noncompliant
        _ = Request.Form[$"prefix.{key}"]; // Noncompliant
        _ = Request.Form.Get($"prefix.{key}"); // Noncompliant
        _ = Request.Form.GetValues($"prefix.{key}"); // Noncompliant
        string localKey = "id";
        _ = Request.Form[localKey]; // FN (Requires SE)

        _ = Request.Form[name: "id"]; // Noncompliant
        _ = Request.Form.Get(name: "id"); // Noncompliant
        _ = Request.Form.GetValues(name: "id"); // Noncompliant
    }

    // Parameterized: Form, QueryString / Request, HttpContext.Request, Request.RequestContext.HttpContext.Request, ControllerContext.RequestContext.HttpContext.Request
    // Implementation: Consider adding a CombinatorialDataAttribute https://stackoverflow.com/a/75531690
    void Compliant(string key)
    {
        // Compliant: Accessing by index is not supported by model binding
        _ = Request.Form[0];
        _ = Request.Form.Get(0);
        _ = Request.Form.GetValues(0);
        // Compliant: Key is not a compile time constant
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
        _ = Request["id"]; // Reads from Cookies, Form, QueryString, and ServerVariables
    }

    void WebFormsHttpRequest(HttpRequest request)
    {
        _ = request.Form["id"]; // Compliant: HttpRequest is used in WebForms pages and is not the same as HttpRequestBase HttpRequest { get; } in a Controller
    }

    // parameterized test: parameters are the different forbidden Request accesses (see above)
    private static void HandleRequest(HttpRequestBase request)
    {
        _ = request.Form["id"]; // Noncompliant: Containing type is a controller
        void LocalFunction()
        {
            _ = request.Form["id"]; // Noncompliant: Containing type is a controller
        }
    }
}

public class CodeBlocksController : Controller
{
    public CodeBlocksController()
    {
        _ = Request.Form["id"]; // Noncompliant
    }

    public CodeBlocksController(object o) => _ = Request.Form["id"]; // Noncompliant

    HttpRequestBase ValidRequest => Request;
    NameValueCollection Form => Request.Form;

    string P1 => Request.Form["id"]; // Noncompliant
    string P2
    {
        get => Request.Form["id"]; // Noncompliant
        set => Request.Form["id"] = value; // Noncompliant
    }
    string P3
    {
        get
        {
            return Request.Form["id"]; // Noncompliant
        }
        set
        {
            Request.Form["id"] = value; // Noncompliant
        }
    }
    void M1() => _ = Request.Form["id"]; // Noncompliant
    void M2()
    {
        Func<string> f1 = () => Request.Form["id"];  // Noncompliant
        Func<object, string> f2 = x => Request.Form["id"];  // Noncompliant
        Func<object, string> f3 = delegate (object x) { return Request.Form["id"]; };  // Noncompliant
    }
    void M3()
    {
        _ = (true ? Request.Form : Request.QueryString)["id"]; // FN: Noncompliant
        _ = ValidatedRequest().Form["id"]; // Noncompliant
        _ = ValidRequest.Form["id"];
        _ = Form["id"];      //  FN: Noncompliant, requires cross method SE
        _ = this.Form["id"]; //  FN: Noncompliant, requires cross method SE 
        _ = new CodeBlocksController().Form["id"]; //  Compliant

        HttpRequestBase ValidatedRequest() => Request;
    }

    void M4()
    {
        _ = this.Request.Form["id"]; // Noncompliant
        _ = Request?.Form?["id"]; // Noncompliant
        _ = Request?.Form?.GetValues("id"); // Noncompliant
        _ = Request.Form?.GetValues("id"); // Noncompliant
        _ = Request.Form?.GetValues("id")?.ToString(); // Noncompliant
        _ = HttpContext.Request.Form["id"]; // Noncompliant
        _ = Request.RequestContext.HttpContext.Request.Form["id"]; // Noncompliant
        _ = this.ControllerContext.RequestContext.HttpContext.Request.Form["id"]; // Noncompliant
        var r1 = HttpContext.Request; _ = r1.Form["id"]; // Noncompliant
        var r2 = ControllerContext; _ = r2.RequestContext.HttpContext.Request.Form["id"]; // Noncompliant
    }
    ~CodeBlocksController() => _ = Request.Form["id"]; // Noncompliant
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

public class OverridesController : Controller
{
    public void Action()
    {
        _ = Request.Form["id"]; // Noncompliant
    }
    private void Undecidable(HttpContextBase context)
    {
        // Implementation: It might be difficult to distinguish between access to "Request" that originate from overrides vs. "Request" access that originate from action methods.
        // This is especially true for "Request" which originate from parameters like here. We may need to redeclare such cases as FNs (see e.g HandleRequest above).
        _ = context.Request.Form["id"]; // Undecidable: request may originate from an action method (which supports binding), or from one of the following overrides (which don't).
    }
    private void Undecidable(HttpRequestBase request)
    {
        _ = request.Form["id"]; // Undecidable: request may originate from an action method (which supports binding), or from one of the following overloads (which don't).
    }

    protected override void Initialize(RequestContext requestContext)
    {
        _ = requestContext.HttpContext.Request.Form["id"]; // Compliant: Model binding is not supported here
    }
    protected override void Execute(RequestContext requestContext)
    {
        _ = requestContext.HttpContext.Request.Form["id"]; // Compliant: Model binding is not supported here
    }
    protected override IAsyncResult BeginExecute(RequestContext requestContext, AsyncCallback callback, object state)
    {
        _ = requestContext.HttpContext.Request.Form["id"]; // Compliant: Model binding is not supported here
        return default;
    }
    protected override void OnActionExecuted(ActionExecutedContext filterContext)
    {
        _ = filterContext.HttpContext.Request.Form["id"]; // Compliant: Model binding is not supported here
    }
    protected override void OnActionExecuting(ActionExecutingContext filterContext)
    {
        _ = filterContext.HttpContext.Request.Form["id"]; // Compliant: Model binding is not supported here
    }
    protected override void OnAuthentication(AuthenticationContext filterContext)
    {
        _ = filterContext.HttpContext.Request.Form["id"]; // Compliant: Model binding is not supported here
    }
    protected override void OnAuthenticationChallenge(AuthenticationChallengeContext filterContext)
    {
        _ = filterContext.HttpContext.Request.Form["id"]; // Compliant: Model binding is not supported here
    }
    protected override void OnAuthorization(AuthorizationContext filterContext)
    {
        _ = filterContext.HttpContext.Request.Form["id"]; // Compliant: Model binding is not supported here
    }
    protected override void OnException(ExceptionContext filterContext)
    {
        _ = filterContext.HttpContext.Request.Form["id"]; // Compliant: Model binding is not supported here
    }
    protected override void OnResultExecuted(ResultExecutedContext filterContext)
    {
        _ = filterContext.HttpContext.Request.Form["id"]; // Compliant: Model binding is not supported here
    }
    protected override void OnResultExecuting(ResultExecutingContext filterContext)
    {
        _ = filterContext.HttpContext.Request.Form["id"]; // Compliant: Model binding is not supported here
    }
}

public class OverridesControllerBase : ControllerBase
{
    protected override void Initialize(RequestContext requestContext)
    {
        _ = requestContext.HttpContext.Request.Form["id"]; // Compliant: Model binding is not supported here
    }
    protected override void Execute(RequestContext requestContext)
    {
        _ = requestContext.HttpContext.Request.Form["id"]; // Compliant: Model binding is not supported here
    }
    protected override void ExecuteCore() => throw new NotImplementedException();
}

public class OverridesIController : IController
{
    public void Execute(RequestContext requestContext)
    {
        _ = requestContext.HttpContext.Request.Form["id"]; // Compliant: Model binding is not supported here
    }
}
static class HttpRequestExtensions
{
    // parameterized test: parameters are the different forbidden Request accesses (see above)
    public static void Ext(this HttpRequestBase request)
    {
        _ = request.Form["id"]; // Compliant: Not in a controller
    }
}

class RequestService
{
    public HttpRequestBase Request { get; }

    // parameterized test: parameters are the different forbidden Request accesses (see above)
    public void HandleRequest(HttpRequestBase request)
    {
        _ = Request.Form["id"]; // Compliant: Not in a controller
        _ = request.Form["id"]; // Compliant: Not in a controller
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