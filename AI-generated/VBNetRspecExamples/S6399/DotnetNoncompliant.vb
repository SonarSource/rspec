Imports System.Xml
Imports Microsoft.AspNetCore.Mvc

Public Class S6399DotnetNoncompliant
    Inherits Controller

    Public Async Sub Example(Username As String)
        Dim Writer As XmlWriter = XmlWriter.Create("data.xml")
        Await Writer.WriteRawAsync(
            $"<user>
                <username>{Username}</username> <!-- Noncompliant -->
                <role>user</role>
            </user>"
        )
        Await Writer.DisposeAsync()
    End Sub
End Class

Public Class S6399DotnetNoncompliant2
    Inherits Controller

    Public Async Sub Example(Username As String)
        Dim Doc As New XmlDocument()
        Dim User As XmlElement = Doc.CreateElement("user")
        Doc.AppendChild(User)

        User.InnerXml = $"
            <username>{Username}</username> <!-- Noncompliant -->
            <role>user</role>"
        Doc.Save("data.xml")
    End Sub
End Class
