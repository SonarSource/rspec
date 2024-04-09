using Microsoft.AspNetCore.Mvc;

WebApplication app = null;
// UseSwagger is not called

namespace Things
{
    [ApiController]
    public class Baseline : ControllerBase
    {
        [HttpGet("foo")]
        public IActionResult NoAttribute() => BadRequest(); // Compliant, not in Swagger context
    }
}