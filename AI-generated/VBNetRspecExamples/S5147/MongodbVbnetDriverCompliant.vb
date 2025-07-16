Imports Microsoft.AspNetCore.Mvc
Imports MongoDB.Driver
Imports MongoDB.Bson
Imports System.Threading.Tasks

Public Class Message
    Public Property Id As ObjectId
    Public Property Username As String
    Public Property Content As String
End Class

<ApiController>
<Route("Example")>
Public Class S5147MongodbVbnetDriverCompliant
    Inherits ControllerBase

    Private ConnectionString As String
    
    <Route("Example")>
    Public Async Function Example() As Task(Of String)
        Dim Client = New MongoClient(ConnectionString)
        Dim Database = Client.GetDatabase("example")
        Dim Collection = Database.GetCollection(Of Message)("messages")

        Dim FilterDefinition = Builders(Of Message).Filter.Eq(Function(m) m.Username, "Example")

        Dim Results = Await Collection.FindAsync(FilterDefinition)
        Return "Complete"
    End Function
End Class
