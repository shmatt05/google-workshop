$(document).ready(function() {

    $('div').on('submit','#signup',  function(e) {

        var postData = $(this).serializeArray();
        var formURL = $(this).attr("action");
        $.ajax(
            {
                url : formURL,
                type: "POST",
                data : postData,
                success:function(data, textStatus, jqXHR)
                {
                    alert(data + " " + textStatus + " " + jqXHR);
                },
                error: function(jqXHR, textStatus, errorThrown)
                {
                    //if fails
                }
            });
        e.preventDefault(); //STOP default action

    });
});

//    $("#signup").on("submit",function(e) {
//
//            var postData = $(this).serializeArray();
//            var formURL = $(this).attr("action");
//            $.ajax(
//                {
//                    url : formURL,
//                    type: "POST",
//                    data : postData,
//                    success:function(data, textStatus, jqXHR)
//                    {
//                        alert(data + " " + textStatus + " " + jqXHR);
//                    },
//                    error: function(jqXHR, textStatus, errorThrown)
//                    {
//                        //if fails
//                    }
//                });
//            e.preventDefault(); //STOP default action
//
//        });
//});

$(window).ready(function(){
        document.getElementById('classkey').value = classID;

});