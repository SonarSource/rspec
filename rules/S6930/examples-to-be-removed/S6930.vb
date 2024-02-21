Imports Microsoft.AspNetCore.Mvc

<Route("A\[controller]")> ' // Noncompliant {{Replace this `\` with `/`.}}
Public Class BackslashOnController
'        ^@-1
    Inherits Controller
End Class

Public Class BackslashOnAction
    Inherits Controller

    <Route("A\[action]")> ' Noncompliant
    Public Function Index() As IActionResult
    '        ^@-1
        Return View()
    End Function
End Class