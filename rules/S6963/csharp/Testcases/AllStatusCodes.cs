using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Mvc.ModelBinding;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Net.Http.Headers;

WebApplication app = null;
app.UseSwagger(); // Necessary for the rule to raise

[ApiController]
public class AllTargetCodes : Controller
{
    #region COMPLIANT

    [HttpGet("foo")]
    public IActionResult ReturnsOk() => Ok(); // Compliant - 200

    [HttpGet("foo")]
    public IActionResult ReturnsOk2() => Ok(null); // Compliant - 200

    [HttpGet("foo")]
    public IActionResult ReturnsContent() => Content(""); // Compliant - 200

    [HttpGet("foo")]
    public IActionResult ReturnsContent2() => Content("", ""); // Compliant - 200

    [HttpGet("foo")]
    public IActionResult ReturnsContent3() => Content("", default(MediaTypeHeaderValue)); // Compliant - 200

    [HttpGet("foo")]
    public IActionResult ReturnsContent4() => Content("", "", null); // Compliant - 200

    public IActionResult ReturnFile() => File("", ""); // Compliant - 200

    public IActionResult ReturnPhysicalFile() => PhysicalFile("", ""); // Compliant - 200

    #endregion

    #region 2XX

    [HttpGet("foo")]
    public IActionResult ReturnsCreated() => // Noncompliant - 201
       Created(); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsCreated2() => // Noncompliant - 201
       Created("uri", null); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsCreated3() => // Noncompliant - 201
       Created(default(Uri), null); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsCreatedAtAction() => // Noncompliant - 201
       CreatedAtAction("actionName", null); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsCreatedAtAction2() => // Noncompliant - 201
       CreatedAtAction("actionName", null, null); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsCreatedAtAction3() => // Noncompliant - 201
       CreatedAtAction("actionName", "controllerName", null, null); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsCreatedAtRoute() => // Noncompliant - 201
       CreatedAtRoute("routeName", null); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsCreatedAtRoute2() => // Noncompliant - 201
       CreatedAtRoute(null, null); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsCreatedAtRoute3() => // Noncompliant - 201
       CreatedAtRoute("routeName", null, null); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsAccepted() => // Noncompliant - 202
        Accepted(); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsAccepted2() => // Noncompliant - 202
        Accepted(default(object)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsAccepted3() => // Noncompliant - 202
        Accepted(default(Uri)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsAccepted4() => // Noncompliant - 202
        Accepted("uri"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsAccepted5() => // Noncompliant - 202
        Accepted("uri", null); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsAccepted6() => // Noncompliant - 202
        Accepted(default(Uri), null); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsAcceptedAtAction() => // Noncompliant - 202
        AcceptedAtAction("actionName"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsAcceptedAtAction2() => // Noncompliant - 202
        AcceptedAtAction("actionName", "controllerName"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsAcceptedAtAction3() => // Noncompliant - 202
        AcceptedAtAction("actionName", default(object)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsAcceptedAtAction4() => // Noncompliant - 202
        AcceptedAtAction("actionName", "controllerName", null); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsAcceptedAtAction5() => // Noncompliant - 202
        AcceptedAtAction("actionName", "controllerName", null, null); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsAcceptedAtRoute() => // Noncompliant - 202
        AcceptedAtRoute(default(object)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsAcceptedAtRoute2() => // Noncompliant - 202
        AcceptedAtRoute("routeName"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsAcceptedAtRoute3() => // Noncompliant - 202
        AcceptedAtRoute("routeName", null); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsAcceptedAtRoute4() => // Noncompliant - 202
        AcceptedAtRoute(default(object), null); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsAcceptedAtRoute5() => // Noncompliant - 202
        AcceptedAtRoute("routeName", null, null); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsNoContent() => // Noncompliant - 204
        NoContent(); // Secondary

    #endregion

    #region 3XX

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectPermanent() => // Noncompliant - 301
        RedirectPermanent("url"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsLocalRedirectPermanent() => // Noncompliant - 301
        LocalRedirectPermanent("url"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnRedirectToActionPermanent() => // Noncompliant - 301
        RedirectToActionPermanent(""); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnRedirectToActionPermanent2() => // Noncompliant - 301
        RedirectToActionPermanent("", default(object)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnRedirectToActionPermanent3() => // Noncompliant - 301
        RedirectToActionPermanent("", ""); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnRedirectToActionPermanent4() => // Noncompliant - 301
        RedirectToActionPermanent("", "", default(object)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnRedirectToActionPermanent5() => // Noncompliant - 301
        RedirectToActionPermanent("", "", ""); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnRedirectToActionPermanent6() => // Noncompliant - 301
        RedirectToActionPermanent("", "", "", ""); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToRoutePermanent() => // Noncompliant - 302
    RedirectToRoutePermanent("url"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToRoutePermanent2() => // Noncompliant - 302
        RedirectToRoutePermanent(default(object)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToRoutePermanent3() => // Noncompliant - 302
        RedirectToRoutePermanent("", default(object)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToRoutePermanent4() => // Noncompliant - 302
        RedirectToRoutePermanent("", ""); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToRoutePermanent5() => // Noncompliant - 302
        RedirectToRoutePermanent("", "", ""); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToPagePermanent() => // Noncompliant - 301
        RedirectToPagePermanent("url"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToPagePermanent2() => // Noncompliant - 301
        RedirectToPagePermanent("", default(object)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToPagePermanent3() => // Noncompliant - 301
        RedirectToPagePermanent("", ""); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToPagePermanent4() => // Noncompliant - 301
        RedirectToPagePermanent("", "", ""); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToPagePermanent5() => // Noncompliant - 301
        RedirectToPagePermanent("", "", "", ""); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToPage() => // Noncompliant - 302
        RedirectToPage("url"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToPage2() => // Noncompliant - 302
        RedirectToPage("", default(object)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToPage3() => // Noncompliant - 302
        RedirectToPage("", ""); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToPage4() => // Noncompliant - 302
        RedirectToPage("", "", default(object)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToPage5() => // Noncompliant - 302
        RedirectToPage("", "", ""); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToPage6() => // Noncompliant - 302
        RedirectToPage("", "", "", ""); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirect() => // Noncompliant - 302
        Redirect("url"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsLocalRedirect() => // Noncompliant - 302
        LocalRedirect("url"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToAction() => // Noncompliant - 302
        RedirectToAction(); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToAction2() => // Noncompliant - 302
        RedirectToAction("actionName"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToAction3() => // Noncompliant - 302
        RedirectToAction("actionName", default(object)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToAction4() => // Noncompliant - 302
        RedirectToAction("actionName", "controllerName"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToAction5() => // Noncompliant - 302
        RedirectToAction("actionName", "controllerName", default(object)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToAction6() => // Noncompliant - 302
        RedirectToAction("actionName", "controlloerName", "fragment"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToAction7() => // Noncompliant - 302
        RedirectToAction("", "", "", ""); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToRoute() => // Noncompliant - 302
        RedirectToRoute("url"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToRoute2() => // Noncompliant - 302
        RedirectToRoute(default(object)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToRoute3() => // Noncompliant - 302
        RedirectToRoute("", default(object)); // Secondary


    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToRoute4() => // Noncompliant - 302
        RedirectToRoute("", ""); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToRoute5() => // Noncompliant - 302
        RedirectToRoute("", "", ""); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToRoutePreserveMethod() => // Noncompliant - 307
        RedirectToRoutePreserveMethod(); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectPreserveMethod() => // Noncompliant - 307
        RedirectPreserveMethod("url"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsLocalRedirectPreserveMethod() => // Noncompliant - 307
        LocalRedirectPreserveMethod(""); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToActionPreserveMethod() => // Noncompliant - 307
        RedirectToActionPreserveMethod(); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToPagePreserveMethod() => // Noncompliant - 307
        RedirectToPagePreserveMethod(""); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectPermanentPreserveMethod() => // Noncompliant - 308
        RedirectPermanentPreserveMethod("url"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsLocalRedirectPermanentPreserveMethod() => // Noncompliant - 308
        LocalRedirectPermanentPreserveMethod("url"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToActionPermanentPreserveMethod() => // Noncompliant - 308
        RedirectToActionPermanentPreserveMethod(); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToRoutePermanentPreserveMethod() => // Noncompliant - 308
        RedirectToRoutePermanentPreserveMethod(); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsRedirectToPagePermanentPreserveMethod() => // Noncompliant - 308
        RedirectToPagePermanentPreserveMethod(""); // Secondary

    #endregion

    #region 4XX

    [HttpGet("foo")]
    public IActionResult ReturnsBadRequest() => // Noncompliant - 400
        BadRequest(); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsValidationProblem() => // Noncompliant - 400
        ValidationProblem(); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsValidationProblem2() => // Noncompliant - 400
        ValidationProblem(default(ValidationProblemDetails)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsValidationProblem3() => // Noncompliant - 400
        ValidationProblem(default(ModelStateDictionary)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsUnauthorized() => // Noncompliant - 401
        Unauthorized(); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsChallenge() => // Noncompliant - [depends on the configured IAuthenticationService, usually 401 or 403]
        Challenge(); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsChallenge2() => // Noncompliant - [depends on the configured IAuthenticationService, usually 401 or 403]
        Challenge("scheme1", "scheme2"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsChallenge3() => // Noncompliant - [depends on the configured IAuthenticationService, usually 401 or 403]
        Challenge(default(AuthenticationProperties)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsChallenge4() => // Noncompliant - [depends on the configured IAuthenticationService, usually 401 or 403]
        Challenge(default(AuthenticationProperties), "scheme1", "scheme2"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsForbid() => // Noncompliant - usually 403
        Forbid(); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsForbid2() => // Noncompliant - usually 403
        Forbid("scheme1", "scheme2"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsForbid3() => // Noncompliant - usually 403
        Forbid(default(AuthenticationProperties)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsForbid4() => // Noncompliant - usually 403
        Forbid(default(AuthenticationProperties), "scheme1", "scheme2"); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsNotFound() => // Noncompliant - 404
        NotFound(); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsNotFound2() => // Noncompliant - 404
        NotFound(null); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsValidationProblem4() => // Noncompliant - 404
        ValidationProblem(statusCode: 404); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsConflict() => // Noncompliant - 409
        Conflict(); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsConflict2() => // Noncompliant - 409
        Conflict(default(object)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsConflict3() => // Noncompliant - 409
        Conflict(default(ModelStateDictionary)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsUnprocessableEntity() => // Noncompliant - 422
        UnprocessableEntity(); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsUnprocessableEntity2() => // Noncompliant - 422
        UnprocessableEntity(default(object)); // Secondary

    [HttpGet("foo")]
    public IActionResult ReturnsUnprocessableEntity3() => // Noncompliant - 422
        UnprocessableEntity(default(ModelStateDictionary)); // Secondary

    #endregion
}