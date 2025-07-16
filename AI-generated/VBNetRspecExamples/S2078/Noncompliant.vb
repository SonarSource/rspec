Imports Microsoft.AspNetCore.Mvc
Imports System.DirectoryServices

Public Class S2078DotnetNoncompliant
    Inherits Controller

    Public Function Authenticate(User As String, Pass As String) As IActionResult
        Dim Directory As New DirectoryEntry("LDAP://ou=system")
        Dim Search As New DirectorySearcher(Directory)

        Search.Filter = "(&(uid=" + User + ")(userPassword=" + Pass + "))"

        Return Json(Search.FindOne() IsNot Nothing)
    End Function
End Class
