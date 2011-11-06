jQuery(window).ready(function(){
    jQuery("#btnInit").click(initiate_geolocation);
})

    function initiate_geolocation() {
        if (navigator.geolocation)
        {
            navigator.geolocation.getCurrentPosition(handle_geolocation_query, handle_errors);
        }
        else
        {
            yqlgeo.get('visitor', normalize_yql_response); //change to Roger's new thing
        }
    }

    function handle_errors(error)
    {
        switch(error.code)
        {
            case error.PERMISSION_DENIED: alert("user did not share geolocation data");
            break;

            case error.POSITION_UNAVAILABLE: alert("could not detect current position");
            break;

            case error.TIMEOUT: alert("retrieving position timedout");
            break;

            default: alert("unknown error");
            break;
        }
    }

    function normalize_yql_response(response)  
    {  
        if (response.error)  
        {  
            var error = { code : 0 };  
            handle_error(error);  
            return;  
        }  
  
        var position = {  
            coords :  
            {  
                latitude: response.place.centroid.latitude,  
                longitude: response.place.centroid.longitude  
            },  
            address :  
            {  
                city: response.place.locality2.content,  
                region: response.place.admin1.content,  
                country: response.place.country.content  
            }  
        };  
  
        handle_geolocation_query(position);  
    }

	function handle_geolocation_query(position)
	{
        $("#lat").html(Math.abs([position.coords.latitude - 37.871667]));
        $("#long").html(position.coords.longitude);
 
       if (Math.abs([position.coords.latitude - 37.871667]) < .27 && Math.abs([position.coords.longitude - -122.272778]) < .27)
         {alert("berkeley")}
       else if (Math.abs([position.coords.latitude - 440.441667]) < .27 && Math.abs([position.coords.longitude - -80]) < .27)
         {alert("pittsburgh")}
       else
         {alert("too far away")}


	}

    //+-0.27 degrees  Pittsburgh: 440.441667, -80,  Berkeley: 37.871667, -122.272778