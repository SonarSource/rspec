Imports Microsoft.AspNetCore.Mvc
Imports System.Xml

Namespace S2091
    Public Class Noncompliant
        Inherits Controller

        <HttpGet>
        Public Function Authenticate(User As String, Pass As String) As IActionResult
            Dim Doc As New XmlDocument()

            Dim Expression As String = "/users/user[@name='" + User + "' and @pass='" + Pass + "']"

            Return Json(Doc.SelectSingleNode(Expression) IsNot Nothing)
        End Function
    End Class
End Namespace
