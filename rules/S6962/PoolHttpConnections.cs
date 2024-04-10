using Microsoft.AspNetCore.Mvc;
using System.IO;

[ApiController]
[Route("Hello")]
public class SomeController : ControllerBase
{
    private readonly IHttpClientFactory _clientFactory;
    private HttpClient clientField = new HttpClient();                     // Compliant, it can be reused between actions
    private HttpClient ClientProperty { get; set; } = new HttpClient();    // Compliant, it can be reused between actions
    private HttpClient ClientPropertyAccessor { get => new HttpClient(); } // Noncompliant
    //                                                 ^^^^^^^^^^^^^^^^
    private HttpClient ClientPropertyAccessorArrow => new HttpClient();    // Noncompliant
    //                                                ^^^^^^^^^^^^^^^^

    [HttpGet("foo")]
    public async Task<string> Foo()
    {
        using var clientA = new HttpClient();                    //Noncompliant
        //                  ^^^^^^^^^^^^^^^^        
        await clientA.GetStringAsync("");      
    
        using (var clientB = new HttpClient())                   //Noncompliant
        {      
            await clientB.GetStringAsync("");      
        }      
    
        var client = new HttpClient();                            // Noncompliant
        client = new();                                           // Noncompliant
        clientField = new HttpClient();                           // Noncompliant
        ClientProperty = new HttpClient();                        // Noncompliant
        var local = new HttpClient();                             // Noncompliant
        local = new System.Net.Http.HttpClient();                 // Noncompliant
        var fromMethod = CreateClient();                          // Noncompliant
     
        local = ClientPropertyAccessor;                           // Compliant
        clientField ??= new HttpClient();                         // Compliant
        using var pooledClient = _clientFactory.CreateClient();   // Compliant
 
        // Lambda
        _ = new Lazy<HttpClient>(() => new HttpClient());         // Compliant

        // Conditional code
        if (true) _ = new HttpClient();
        switch (true) { case true: _ = new HttpClient(); break; } // Compliant
        _ = true switch { true => new HttpClient() };             // Compliant
        _ = true ? new HttpClient() : null;                       // Compliant

        return "bar";
    }
    private static HttpClient CreateClient()
    {
        return new HttpClient();
    }
}

#region Constructor initializers UTs

public class C(HttpClient client);
public class D(HttpClient client) : C(new HttpClient()) // Compliant
{
    public D() : this(new HttpClient()) { }            // Compliant
}
public class E : C
{
    public E() : base(new HttpClient()) { }            // Compliant
}

# endregion

