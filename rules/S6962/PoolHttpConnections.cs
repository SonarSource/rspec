using Microsoft.AspNetCore.Mvc;

[ApiController]
[Route("Hello")]
public class SomeController : ControllerBase
{
    private HttpClient clientField = new HttpClient();                     // Compliant, it can be reused between actions
    private HttpClient ClientProperty { get; set; } = new HttpClient();    // Compliant, it can be reused between actions
    private HttpClient ClientPropertyAccessor { get => new HttpClient(); } // Noncompliant
    private HttpClient ClientPropertyAccessorArrow => new HttpClient();    // Noncompliant

    [HttpGet("foo")]
    public async Task<string> Foo()
    {
        using var clientA = new HttpClient();      //Noncompliant
        await clientA.GetStringAsync("");

        using (var clientB = new HttpClient())    //Noncompliant
        {
            await clientB.GetStringAsync("");
        }

        var clienC = new HttpClient();            // Noncomlpiant
        clientField = new HttpClient();           // Noncompliant
        ClientProperty = new HttpClient();        // Noncompliant
        var local = new HttpClient();             // Noncompliant
        local = new System.Net.Http.HttpClient(); // Noncompliant
        local = ClientPropertyAccessor;           // Noncompliant
        var fromMethod = CreateClient();          // Noncompliant

        return "bar";
    }

    private static HttpClient CreateClient()
    {
        return new HttpClient();
    }
}