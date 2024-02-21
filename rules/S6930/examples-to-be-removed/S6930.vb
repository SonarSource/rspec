<Route("A\[controller]")> ' // Noncompliant {{Replace this `\` with `/`.}}
'        ^
Public Class BackslashOnController
    Inherits Controller
End Class

Public Class BackslashOnAction
    Inherits Controller

    <Route("A\[action]")> ' Noncompliant
    '        ^
    Public Function Index() As IActionResult
        Return View()
    End Function
End Class