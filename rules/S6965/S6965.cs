using Microsoft.AspNetCore.Mvc;

[ApiController]
public class NoncompliantController : ControllerBase
{
    [Route("foo")]
    public string FooGet() => "Hi";                 // Noncompliant
    //            ^^^^^^

    public int FooPost([FromBody] string id) =>
        StatusCodes.Status200OK;                   // Noncompliant
}


[ApiController]
public class CompliantController : ControllerBase
{
    [HttpGet("foo")]
    public string FooGet() => "Hi";  

    [HttpPost("foo")]
    public int FooPost([FromBody] string id) =>
        StatusCodes.Status200OK;

    [Route("foo")]
    [HttpDelete]
    public int FooDelete([FromBody] string id) =>
        StatusCodes.Status200OK;

    [Route("Error")]
    [ApiExplorerSettings(IgnoreApi = true)]
    public int FooError([FromBody] string id) =>  // Compliant, it's annotated with [ApiExplorerSettings(IgnoreApi = true)]
        StatusCodes.Status200OK;
}

[ApiController]
[ApiExplorerSettings(IgnoreApi = true)]
public class ExcludedFromOpenAPIController : ControllerBase
{
    [Route("foo")]                        
    public string FooGet() => "Hi";                 // Compliant, controller is annotated with [ApiExplorerSettings(IgnoreApi = true)]           

    public int FooPost([FromBody] string id) =>    // Compliant, controller is annotated with [ApiExplorerSettings(IgnoreApi = true)]
        StatusCodes.Status200OK;
}


[ApiController]
internal class NotPublic : ControllerBase
{
    [Route("foo")]
    public string FooGet() => "Hi";   // Compliant, only public classes are considered
}

[NonController]
[ApiController]
public class NotAController : ControllerBase
{
    [Route("foo")]
    public string FooGet() => "Hi";    // Compliant, excluded by controller the attribute
}

public class NotApiController : ControllerBase
{
    [Route("foo")]
    public string FooGet() => "hi";    // Compliant, only classes annotated with "ApiController" are considered
}