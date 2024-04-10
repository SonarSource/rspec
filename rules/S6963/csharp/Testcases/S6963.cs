using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Infrastructure;
using Microsoft.AspNetCore.Mvc.ModelBinding;

WebApplication app = null;
app.UseSwagger(); // Necessary for the rule to raise

namespace Things
{
    [ApiController]
    public class Baseline : ControllerBase
    {
        [HttpGet("foo")]
        [ProducesResponseType(StatusCodes.Status400BadRequest)]
        public IActionResult HasCorrectAttribute() => BadRequest(); // Compliant

        [HttpGet("foo")]
        [ProducesResponseType(400)]
        public IActionResult HasCorrectAttributeWithNumber() => BadRequest(); // Compliant

        [HttpGet("foo")]
        [ProducesResponseType(typeof(object), StatusCodes.Status400BadRequest)]
        public IActionResult HasCorrectAttributeWithTpe() => BadRequest(); // Compliant

        [HttpGet("foo")]
        [ProducesResponseType(typeof(object), StatusCodes.Status400BadRequest, "application/xml")]
        public IActionResult HasCorrectAttributeWithContentType() => BadRequest(); // Compliant

        [HttpGet("foo")]
        [ProducesResponseType<int>(StatusCodes.Status400BadRequest)]
        public IActionResult HasCorrectAttributeGeneric() => BadRequest(); // Compliant

        [HttpGet("foo")]
        [ProducesResponseType<int>(StatusCodes.Status400BadRequest, "application/json")]
        public IActionResult HasCorrectAttributeWithContentTypeGeneric() => BadRequest(); // Compliant

        [HttpGet("foo")]
        public IActionResult NoAttribute() => // Noncompliant {{Annotate this method with ProducesResponseType for "BadRequest".}}
        //                   ^^^^^^^^^^^
            BadRequest(); // Secondary
        //  ^^^^^^^^^^

        [HttpGet("foo")]
        [ProducesResponseType(StatusCodes.Status418ImATeapot)]
        public IActionResult HasWrongAttribute() => // Noncompliant {{Annotate this method with ProducesResponseType for "BadRequest".}}
        //                   ^^^^^^^^^^^^^^^^^
            BadRequest(); // Secondary
        //  ^^^^^^^^^^

        [HttpGet("foo")]
        [ProducesResponseType(418)]
        public IActionResult HasAttributeWithWrongNumber() => // Noncompliant {{Annotate this method with ProducesResponseType for "BadRequest".}}
        //                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^
            BadRequest(); // Secondary
        //  ^^^^^^^^^^

        [HttpGet("foo")]
        [ProducesResponseType(typeof(object), StatusCodes.Status418ImATeapot)]
        public IActionResult HasWrongAttributeWithType() => // Noncompliant
            BadRequest(); // Secondary


        [HttpGet("foo")]
        [ProducesResponseType(typeof(object), StatusCodes.Status418ImATeapot), "application/xml"]
        public IActionResult HasWrongAttributeWithContentType() => // Noncompliant
            BadRequest(); // Secondary

        [HttpGet("foo")]
        [ProducesResponseType<int>(StatusCodes.Status418ImATeapot)]
        public IActionResult HasWrongAttributeGeneric() => // Noncompliant
            BadRequest(); // Secondary

        [HttpGet("foo")]
        [ProducesResponseType<int>(StatusCodes.Status418ImATeapot, "application/json")]
        public IActionResult HasWrongAttributeWithContentTypeGeneric() => // Noncompliant
            BadRequest(); // Secondary

        [Route("foo")]
        public IActionResult NoAttributeWithRoute() => // Noncompliant {{Annotate this method with ProducesResponseType for "BadRequest".}}
            BadRequest(); // Secondary

        /// <response code="400">Some text</response>
        [HttpGet("foo")]
        public IActionResult AnnotatedWithXml() => BadRequest();

        [HttpGet("foo")]
        /// <response code="400">this does not work</response>
        public IActionResult AnnotatedErroneouslyWithXml() => // Noncompliant, response has to be above the attribute.
            BadRequest();

        [HttpGet("foo")]
        protected IActionResult IsNotPublic() => BadRequest(); // Compliant, only public methods are considered
    }

    [ApiController]
    internal class NotPublic : ControllerBase
    {
        [HttpGet("foo")]
        public IActionResult NoAttribute() => BadRequest(); // Compliant, only public classes are considered
    }

    [NonController]
    [ApiController]
    public class NotAController : ControllerBase
    {
        [HttpGet("foo")]
        public IActionResult NoAttribute() => BadRequest(); // Compliant, excluded by the attribute
    }

    public class NotApiController : ControllerBase
    {
        [HttpGet("foo")]
        public IActionResult NoAttribute() => BadRequest(); // Compliant, only classes annotated with "ApiController" are considered
    }

    [ApiController]
    public class MultipleErrorCodes : Controller
    {
        [HttpGet("foo")]
        [ProducesResponseType(StatusCodes.Status400BadRequest)]
        public IActionResult MissOne(bool condition) => // Noncompliant {{Annotate this method with ProducesResponseType for "NotFound".}}
        //                   ^^^^^^^
            condition ? NotFound() : BadRequest(); // Secondary
        //              ^^^^^^^^

        [HttpGet("foo")]
        [ProducesResponseType(StatusCodes.Status302Found)]
        public IActionResult MissesMultiple(bool condition) // Noncompliant [badRequest] {{Annotate this method with ProducesResponseType for "BadRequest".}}
        //                   ^^^^^^^^^^^^^^
        //                   ^^^^^^^^^^^^^^ @-2 [notFound] {{Annotate this method with ProducesResponseType for "NotFound".}}
        {
            if (condition)
            {
                return NotFound(); // Secondary [notFound]
                //     ^^^^^^^^
            }
            else if (condition)
            {
                return BadRequest(); // Secondary [badRequest]
                //     ^^^^^^^^^^
            }

            return Redirect("url");
        }
    }

    [ApiController]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public class AnnotatedAtControllerLevel : ControllerBase
    {

        [HttpGet("foo")]
        public IActionResult Valid() => BadRequest(); // Compliant

        [HttpGet("foo")]
        public IActionResult Invalid() =>  // Noncompliant {{Annotate this method with ProducesResponseType for "NotFound".}}
        //                   ^^^^^^^
            NotFound(); // Secondary
        //  ^^^^^^^^
    }

    [ApiController]
    public class MixedAnnotations : Controller
    {
        /// <response code="404">Some text</response>
        [HttpGet("foo")]
        [ProducesResponseType(StatusCodes.Status400BadRequest)]
        public IActionResult MarkedWithBothXmlAndAttribute(bool condition) => // Compliant
            condition ? BadRequest() : NotFound();

        /// <response code="307">Not found</response>
        /// <response code="409">Conflict</response>
        [HttpGet("foo")]
        [ProducesResponseType(StatusCodes.Status400BadRequest)]
        public IActionResult MarkedWithBothXmlAndAttribute(int condition) => // Noncompliant {{Annotate this method with ProducesResponseType for "NotFound".}}
            condition switch
            {
                1 => RedirectPreserveMethod("url"),
                2 => NotFound(), // Secondary
                //   ^^^^^^^^
                3 => BadRequest(),
                4 => Conflict(),
            };
    }

    [ApiController]
    public class NotReturns : ControllerBase
    {
        [HttpGet("foo")]
        public IActionResult SimpleOk(bool condition) // Compliant, only return statements are checked
        {
            var x1 = BadRequest();
            IActionResult x2 = condition ? NotFound() : NoContent();
            var lambda = () => Redirect("url");
            return Ok();
        }

        [HttpGet("foo")]
        public IActionResult NestedErrorCodes() // Noncompliant {{Annotate this method with ProducesResponseType for "NotFound".}}
        {
            return Ok(BadRequest());    // Conmpliant, we only consider the top node of the return expression
            return Ok(Redirect("url")); // Compliant, same as above

            return NotFound(); // Secondary
            //     ^^^^^^^^
        }
    }

    // For the implementation: If this seems too cumbersome, consider dropping it and documenting it as FN
    [ApiController]
    public class ExplicitErrorCodes_NewObjects : Controller
    {
        [HttpGet("foo")]
        public ObjectResult NewObjectResult() => // Noncompliant
            new ObjectResult(42) { StatusCode = StatusCodes.Status418ImATeapot }; // Secondary

        [HttpGet("foo")]
        public StatusCodeResult NewStatusCodeResult() => // Noncompliant
            new StatusCodeResult(statusCode: 42); // Secondary

        [HttpGet("foo")]
        public IActionResult NewContentResult() => // Noncompliant
            new ContentResult { StatusCode = StatusCodes.Status418ImATeapot }; // Secondary

        [HttpGet("foo")]
        public IActionResult NewRedirectResult() => // Noncompliant
            new RedirectResult("url", permanent: true, preserveMethod: false); // Secondary
    }

    [ApiController]
    public class ExplicitErrorCodes_Methods : ControllerBase
    {
        [HttpGet("foo")]
        public IActionResult StatusCodeMethod() => // Noncompliant
            StatusCode(StatusCodes.Status404NotFound); // Secondary

        [HttpGet("foo")]
        public IActionResult StatusCodeMethodWithValue() => // Noncompliant
            StatusCode(statusCode: 42, null);

        [HttpGet("foo")]
        public IActionResult ProblemMethodWithStatusCode() => // Noncompliant
            Problem(statusCode: StatusCodes.Status418ImATeapot); // Secondary

        [HttpGet("foo")]
        public IActionResult ProblemMethodWithoutStatusCode() => // Compliant
            Problem();
    }
}
