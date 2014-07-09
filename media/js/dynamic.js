//alert('inside dynamic js');


// Replace the normal jQuery getScript function with one that supports
// debugging and which references the script files as external resources
// rather than inline.
jQuery.extend({
    getScript: function(url, callback) {
       var head = document.getElementsByTagName("head")[0];
       var script = document.createElement("script");
       script.src = url;
       
       // Handle Script loading
       {
	   var done = false;
	   
	   // Attach handlers for all browsers
	   script.onload = script.onreadystatechange = function(){
	       if ( !done && (!this.readyState ||
			      this.readyState == "loaded" || this.readyState == "complete") ) {
		   done = true;
		   if (callback)
		       callback();
		   
		   // Handle memory leak in IE
		   script.onload = script.onreadystatechange = null;
	       }
	   };
       }
       head.appendChild(script);

       // We handle everything using the script element injection
       return undefined;
    },
});


$(document).ready( function() {
  /* Update filter_box UI */
  var tab_holder = $(".tabs");
  var current_tab_id = tab_holder.attr('data-current-tab');

  var sort_by = tab_holder.attr('data-current-sort');
  $("#sort_" + sort_by).attr("class","linkActiveSort");

  var sort_li = $('.sort_list li');
  sort_li.each(function(index) {
    if (index != sort_by) {
      $(this).click({tab_num: current_tab_id, sort_by: index}, displayTabContent);
    }
  });

  if (!is_mobile) {
    $(".place_name").hover(
      // Check Callback and Functions at http://docs.jquery.com/How_jQuery_Works
      // for callback with arguments
      function() {
        show_info_dialog(event);
      },
      function() {
      }
    );
  }

} );

var jtw_search_distance = 3;  // mile
var jtw_search;
var jtw_current_search;
var jtw_search_geocode;
var jtw_num_tweets;
var jtw_tweet_lang;
var jtw_widget_refresh_interval;
var deviceAgent = navigator.userAgent;
var is_mobile = deviceAgent.toLowerCase().match(/(iphone|ipod|ipad|webos|android)/);

//function show_info_dialog(event) {
var show_info_dialog = function (event) {
    $("#dialog").dialog('close');
    var target_split_arr = String(event.target.id).split(",");
    var fb_place_id = target_split_arr[0];
    if (target_split_arr.length > 2) {
	var fb_place_long = target_split_arr[1];
	var fb_place_lat = target_split_arr[2];
    }
    FB.api('/' + fb_place_id, function(response) {
      if (!response) {
        dialog_msg = "<p>Page not found.</p>";
        $('#dialog').html(dialog_msg).dialog({title: response['name'], model: true, autoOpen: false, minWidth: 450, position: [event.pageX + 80, event.pageY - 20]}).dialog('open');
        return;
      }

      if ('error' in response && 'code' in response['error'] && response['error']['code'] == 21) {
	  var page_id = response['error']['message'].match(/([\d]+)(?= was migrated to page)/g);
	  var stale_data_url = 'data/stale.py?page_id=' + page_id + '&access_token=' + access_token;
	  $.ajax({url:stale_data_url}).done( function(data) {
		  //alert('ajax get success' + data);
		  if (data != "-1" || data != -1) {
		    $("#tr_" + page_id).remove();
		  }
		  $("#dialog").dialog('close');
		  //$("#tabpage_" + tab_num).append(data);

	      } );
      }
      
      dialog_msg = ""
      if (response['cover'] && response['cover'].source) {
        //dialog_msg += "<img src='"+response['cover'].source+"' alt='image' style='width:40%;height:40%'>"
	dialog_msg += "<img src='"+response['cover'].source+"' alt='image' style='max-width:40%;max-height:40%'>"
      } 
	
      dialog_msg += "<ul>";

      // order keys
      sorted_keys = [];
      // Name already at the top bar
      //if (response['name'])
      //  sorted_keys.push('name');
      //if (response['cover'])
      //  sorted_keys.push('cover');
      if (response['about'])
        sorted_keys.push('about');
      if (response['general_info'])
        sorted_keys.push('general_info');
      if (response['mission'])
        sorted_keys.push('mission');
      if (response['category'])
        sorted_keys.push('category');
      if (response['location'])
        sorted_keys.push('location');
      if (response['phone'])
        sorted_keys.push('phone');
      if (response['website'])
        sorted_keys.push('website');
      if (response['parking'])
        sorted_keys.push('parking');
      if (response['hours'])
        sorted_keys.push('hours');
      if (response['checkins'])
        sorted_keys.push('checkins');
      if (response['likes'])
        sorted_keys.push('likes');

      for (var i in response) {
        if (sorted_keys.indexOf(i) == -1) {
          sorted_keys.push(i);
        }
      }

      for (var idx = 0; idx < sorted_keys.length; idx++) {
        i = sorted_keys[idx];
        switch(i) {
          case "is_published":
          case "id":
          case "is_community_page":
	  case "cover":
          case "talking_about_count":
          case "were_here_count":
          case "description":
          case "general_manager":
          case "culinary_team":
          case "username":
          case "parent_page":
	  case "name":
            break;
          case "location":
            dialog_msg += "<li>Location: ";
	    var address = "";
	    if (response[i]['street'])
	      address += response[i]['street'] + ' ';
	    if (response[i]['city'])
	      address += response[i]['city'] + ' ';
	    if (response[i]['state'])
	      address += response[i]['state'] + ' ';
	    if (response[i]['zip'])
	      address += response[i]['zip'] + ' ';

	    dialog_msg += address + " (<a href='http://maps.google.com/?q=" + address.replace(' ', '+') + 
		"' target='" + address.replace(' ', '+') + "'>Map</a>)";
	    dialog_msg += "</li>\n";	    
            break;
          case "public_transit":
            dialog_msg += "<li>Public Transit: ";
	    if (response[i])
	      dialog_msg += response[i];
	    dialog_msg += "</li>\n";
            break;
          case "parking":
            dialog_msg += "<li>Parking: ";
	    if (response[i]['street'])
	      dialog_msg += 'street ';
	    if (response[i]['lot'])
	      dialog_msg += 'lot ';
	    if (response[i]['valet'])
	      dialog_msg += 'valet ';	    
	    dialog_msg += "</li>\n";
            break;
          case "payment_options":
            dialog_msg += "<li>Payment Options: ";
	    if (response[i]['cash_only'])
	      dialog_msg += 'cash_only ';
	    if (response[i]['visa'])
	      dialog_msg += 'visa ';
	    if (response[i]['amex'])
	      dialog_msg += 'amex ';	    
	    if (response[i]['mastercard'])
	      dialog_msg += 'mastercard ';	    
	    if (response[i]['discover'])
	      dialog_msg += 'discover ';
	    dialog_msg += "</li>\n";
            break;
          case "restaurant_services":
            dialog_msg += "<li>Restaurant Services: ";
	    if (response[i]['catering'])
	      dialog_msg += 'catering ';
	    if (response[i]['delivery'])
	      dialog_msg += 'delivery ';
	    if (response[i]['groups'])
	      dialog_msg += 'groups ';	    
	    if (response[i]['kids'])
	      dialog_msg += 'kids ';
	    if (response[i]['outdoor'])
	      dialog_msg += 'outdoor ';
	    if (response[i]['reserve'])
	      dialog_msg += 'reserve ';
	    if (response[i]['takeout'])
	      dialog_msg += 'takeout ';
	    if (response[i]['waiter'])
	      dialog_msg += 'waiter ';
	    if (response[i]['walkings'])
	      dialog_msg += 'walkings ';
	    dialog_msg += "</li>\n";
            break;
          case "restaurant_specialties":
            dialog_msg += "<li>Restaurant Specialities: ";
	    if (response[i]['breakfast'])
	      dialog_msg += 'breakfast ';
	    if (response[i]['lunch'])
	      dialog_msg += 'lunch ';
	    if (response[i]['dinner'])
	      dialog_msg += 'dinner ';	    
	    if (response[i]['coffee'])
	      dialog_msg += 'coffee ';	    
	    if (response[i]['drinks'])
	      dialog_msg += 'drinks ';
	    dialog_msg += "</li>\n";
            break;
          case "parking":
            dialog_msg += "<li>Parking: ";
	    if (response[i]['street'])
	      dialog_msg += 'street ';
	    if (response[i]['lot'])
	      dialog_msg += 'lot ';
	    if (response[i]['valet'])
	      dialog_msg += 'valet ';	    
	    dialog_msg += "</li>\n";
            break;
          case "hours":
	    dialog_msg += "<li>Hours: <ul>";
            if (typeof(response[i]) == "object") {
              for (var j in response[i]) {
                if (j.search("open") > 0) {
	          dialog_msg += "<li>";
	          dialog_msg += j.substring(0,3) + ": " + response[i][j];
	        } else if (j.search("close") > 0) {
	          dialog_msg += " - " + response[i][j];
	          dialog_msg += "</li>";
	        }
              }
            } else {
              dialog_msg += response[i];
            }
	    dialog_msg += "</ul></li>\n";
            break;
          case "website":
          case "link":
            if (i == 'link') {
	      dialog_msg += "<li>Facebook link: ";  
	    } else {
	      dialog_msg += "<li>" + capitalizeFirstLetter(i) + ": ";  
	    }
	    arr_websites = response[i].split(' ', 3) // max 3 websites
	    for (j = 0; j < arr_websites.length; j++) {
		//alert(arr_websites[j]);
		if (arr_websites[j].substring(0,4) != 'http')
		    arr_websites[j] =  'http://' + arr_websites[j]
		dialog_msg += "<a href='" + arr_websites[j] + "' target='" + arr_websites[j] + "'>" + arr_websites[j] + "</a> ";
	    }
	    dialog_msg += "</li>\n"
            break;
          case "about":
          case "mission":
          case "general_info":
            if (response[i].length > 200) {
		dialog_msg += "<li>" + capitalizeFirstLetter(i) + ": " + response[i].substring(0, 200) + "...</li>\n";
            } else {
		dialog_msg += "<li>" + capitalizeFirstLetter(i) + ": " + response[i] + "</li>\n";
            }
            break;
          default:
            dialog_msg += "<li>";
            if (typeof(response[i]) == "object") {
	      dialog_msg += "<ul>" + capitalizeFirstLetter(i) + ": ";
              for (var j in response[i]) {
	        dialog_msg += "<li>" + capitalizeFirstLetter(j) + ": " + response[i][j] + "</li>";
              }
              dialog_msg += "</ul>";
            } else {
	      dialog_msg +=  capitalizeFirstLetter(i) + ": " + response[i];
            }
            dialog_msg += "</li>\n";
	} // switch(i)
      } // for (var i in response
      dialog_msg += "</ul>";
      dialog_msg += "<div id='tweet_frame'><div id='tweet_widget'></div></div>";
      
      var y = event.pageY - $(window).scrollTop() - 100;
      $('#dialog').html(dialog_msg).dialog({title: response['name'], model: true, autoOpen: false, minWidth: 450, position: ['center', y]}).dialog('open');

      
      /* Load twitter search widget */
      /* widget config */
      //var jtw_divname              = 'jtw_widget1';
      var jtw_divname                = 'tweet_widget';
      jtw_search                 = response['name'];
      jtw_current_search                 = response['name'];
      jtw_search_geocode         = fb_place_lat + ',' + fb_place_long + ',' + jtw_search_distance + 'mi';
      var jtw_width                  = '400px';
      var jtw_height                 = '500px';
      var jtw_scroll                 = 'yes';
      var jtw_widget_background      = '#CFF2FF';
      var jtw_widget_border          = '2px solid #4192AF';
      var jtw_center_widget          = 'yes';
      
      /* tweet styling */
      var jtw_tweet_textcolor        = '';
      var jtw_tweet_background       = 'url(./img/greygrad.png) repeat-x #fff';
      var jtw_tweet_newbackground    = '#ffe';
      var jtw_tweet_border           = '1px solid #4192AF';
      var jtw_tweet_margin           = '5px';
      var jtw_tweet_fontsize         = '12px';
      var jtw_hide_img               = '';
      
      /* search and display config */
      var jtw_pre_html               = '<center><b>' +  response['name'] + '</b></center>';
      var jtw_post_html              = '';
      var jtw_mid_html               = '<hr>';
      jtw_num_tweets             = '10';
      jtw_tweet_lang             = 'en';
      jtw_widget_refresh_interval= 20;
      $.getScript("/lmedia/js/widget_formatted.js");
    }); // FB.api'
  } // function show_info_dialog

  function capitalizeFirstLetter(str) {
    var ret_str = str.charAt(0).toUpperCase() + str.slice(1);
    return ret_str.replace('_', ' ')
  }

  
