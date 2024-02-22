using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using System.Linq;
using System.Threading.Tasks;

namespace WebApplication1.Controllers;

public class TestController : Controller
{
    public IActionResult Post()
    {
        _ = Request.Form["id"];                           // Noncompliant {{Use model binding instead of accessing the raw request data}}
        //          ^^^^
        _ = Request.Form.TryGetValue("id", out _);        // Noncompliant {{Use model binding instead of accessing the raw request data}}
        //          ^^^^
        _ = Request.Form.ContainsKey("id");               // Noncompliant {{Use model binding instead of accessing the raw request data}}
        //          ^^^^
        _ = Request.Form.Files;                           // Noncompliant {{Use IFormFile or IFormFileCollection binding instead}}
        //               ^^^^^
        _ = Request.Query["id"];                          // Noncompliant {{Use model binding instead of accessing the raw request data}}
        //          ^^^^^
        _ = Request.Query.TryGetValue("id", out _);       // Noncompliant {{Use model binding instead of accessing the raw request data}}
        //          ^^^^^
        _ = Request.RouteValues["id"];                    // Noncompliant {{Use model binding instead of accessing the raw request data}}
        //          ^^^^^^^^^^^
        _ = Request.RouteValues.TryGetValue("id", out _); // Noncompliant {{Use model binding instead of accessing the raw request data}}
        //          ^^^^^^^^^^^
        _ = Request.Form.Files["file"];                   // Noncompliant {{Use IFormFile or IFormFileCollection binding instead}}
        //               ^^^^^
        _ = Request.Form.Files[0];                        // Noncompliant {{Use IFormFile or IFormFileCollection binding instead}}
        //               ^^^^^
        _ = Request.Form.Files.Any();                     // Noncompliant {{Use IFormFile or IFormFileCollection binding instead}}
        //               ^^^^^
        _ = Request.Form.Files.Count;                     // Noncompliant {{Use IFormFile or IFormFileCollection binding instead}}
        //               ^^^^^
        _ = Request.Form.Files.GetFile("file");           // Noncompliant {{Use IFormFile or IFormFileCollection binding instead}}
        //               ^^^^^
        _ = Request.Form.Files.GetFiles("file");          // Noncompliant {{Use IFormFile or IFormFileCollection binding instead}}
        //               ^^^^^
        return default;
    }

    // Parameterized for "Form", "Query" and "RouteValues"
    void NoncompiantKeyVariations()
    {
        _ = Request.Form[@"key"];                                 // Noncompliant
        _ = Request.Form.TryGetValue(@"key", out _);              // Noncompliant
        _ = Request.Form["""key"""];                              // Noncompliant
        _ = Request.Form.TryGetValue("""key""", out _);           // Noncompliant
        
        const string key = "id";
        _ = Request.Form[key];                                    // Noncompliant
        _ = Request.Form.TryGetValue(key, out _);                 // Noncompliant
        _ = Request.Form[$"prefix.{key}"];                        // Noncompliant
        _ = Request.Form.TryGetValue($"prefix.{key}", out _);     // Noncompliant
        _ = Request.Form[$"""prefix.{key}"""];                    // Noncompliant
        _ = Request.Form.TryGetValue($"""prefix.{key}""", out _); // Noncompliant

        _ = Request.Form[key: "id"];                              // Noncompliant
        _ = Request.Form.TryGetValue(value: out _, key: "id");    // Noncompliant
    }

    // Parameterized for "Form", "Query", and "RouteValues"
    async Task Compliant(string key)
    {
        _ = Request.Form.Keys;
        _ = Request.Form.Count;
        foreach (var kvp in Request.Form) { }
        _ = Request.Form.Select(x => x);
        _ = Request.Form[key];                // Compliant: The accessed key is not a compile time constant
        _ = Request.Cookies["coockie"];       // Compliant: Cookies are not bound by default
        _ = Request.QueryString;              // FN: QueryString is the whole raw string. We should raise for Request.QueryString.Split() calls
        _ = await Request.ReadFormAsync();    // Compliant: This might be used for optimization purposes e.g. conditional form value access.
    }

    // parameterized test: parameters are the different forbidden Request accesses (see above)
    private static void HandleRequest(HttpRequest request)
    {
        _ = request.Form["id"]; // Noncompliant: Containing type is a controller
        void LocalFunction()
        {
            _ = request.Form["id"]; // Noncompliant: Containing type is a controller
        }
        static void StaticLocalFunction(HttpRequest request)
        {
            _ = request.Form["id"]; // Noncompliant: Containing type is a controller
        }
    }
}

// parameterized test: Repeat for Controller, ControllerBase, MyBaseController, MyBaseBaseController base classes
public class MyBaseController : ControllerBase { }
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
