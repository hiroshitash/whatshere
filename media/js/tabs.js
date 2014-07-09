function getURLParameter(name) {
    return decodeURI(
      (RegExp(name + '=' + '(.+?)(&|$)').exec(location.search)||[,null])[1]
    );
}


$(document).ready( function() {
    var wh_q = getURLParameter('wh_q');
    var sort_by = getURLParameter('sort_by');
    var tab_index_show;

    if (wh_q == 'recommend') {
	tab_index_show = 1;
    } else if (wh_q == 'deal') {
	tab_index_show = 2;
    } else {
	tab_index_show = 0;
    }

    if (sort_by.length == 0 || sort_by == 'null' || sort_by == 'distance')
	sort_by = 0;
    else
	sort_by = 1;

    // get tab container
    var container = $('#tabContainer');
    var navitem = $(".tabs ul li", container).eq(tab_index_show);
    var tab_holder = $(".tabs", container);

    tab_holder.attr('data-current-tab', tab_index_show);
    tab_holder.attr('data-current-sort', sort_by);
    tab_holder.attr('data-current-page', 1);
    navitem.attr('class', 'tabActiveHeader');

    var pages = $('.tabpage', container);
    pages.each(function(index) {
	    if (index != tab_index_show) {
		$(this).hide();
	    }
	});

    // display tab content when tabs are clicked
    var tabs = $(".tabs ul li", container);
    tabs.each(function(index) {
	    //tabs.click({page_num: 1}, displayTabContent);
	    //tabs[index].click({tab_num: index}, displayTabContent);
	    /*
	    if (index == 0) {
		wh_q = 'checkin';
	    } else if (index == 1) {
		wh_q = 'recommend';
	    } else {
		wh_q = 'deal';
	    }
	    */
	    if (tabs[index].innerText == 'Recommendations' || tabs[index].innerText == 'Recommends') {
		wh_q = 'recommend';
	    } else if (tabs[index].innerText == 'Deals') {
		wh_q = 'deal';
	    } else {
		wh_q = 'checkin';
	    }
	    $(this).click({tab_num: index, sort_by: -1, wh_q: wh_q}, displayTabContent);
	});


    // active select for sort
    $("#sort_" + sort_by).attr("class","linkActiveSort");

    // display tab content with sort_by when sort lists are clicked
    var sort_li = $('.sort_list li');
    sort_li.each(function(index) {
      if (index != sort_by) {
	  /*
	  if (tab_index_show == 0) {
	      wh_q = 'checkin';
	  } else if (tab_index_show == 1) {
	      wh_q = 'recommend';
	  } else {
	      wh_q = 'deal';
	      }
	  */
	  if (tabs[index].innerText == 'Recommendations') {
	      wh_q = 'recommend';
	  } else if (tabs[index].innerText == 'Deals') {
	      wh_q = 'deal';
	  } else {
	      wh_q = 'checkin';
	  }

	  $(this).click({tab_num: tab_index_show, sort_by: index, wh_q: wh_q}, displayTabContent);
      }
    });

    dropdown_li = $("ul.dropdown li");
    if (dropdown_li.length > 0) {
      dropdown_li.hover(
        function(){
	  $('ul:first',this).css('display', 'block');
	}, 
	function(){    
	  $('ul:first',this).css('display', 'none');
	}
      );
    }

} );


// on click of one of tabs
function displayTabContent(event) {
    //    var page_num = event.data.page_num;
    //    var tab_num = $(this).attr('id').split("_")[1];
    if (event.data.sort_by == -1) {
      var tab_holder = $(".tabs");
      event.data.sort_by = tab_holder.attr('data-current-sort')
    }
    displayPage(event.data.tab_num, event.data.page_num, event.data.sort_by, event.data.wh_q);
}

function displayPage(tab_num, page_num, sort_by, wh_q) {
    // Get the user agent string
    var deviceAgent = navigator.userAgent;
    // Set var to iOS device name or null
    var is_mobile = deviceAgent.toLowerCase().match(/(iphone|ipod|ipad|webos|android)/);

    if (!is_mobile) {
	$("#dialog").dialog('close');
    }

    var tab_holder = $(".tabs");
    var current_tab_id = tab_holder.attr('data-current-tab');
    var current_page_id = tab_holder.attr('data-current-tab' + current_tab_id + '-page');
    var current_tab_header = $("#tabHeader_" + current_tab_id);

    current_tab_header.removeAttr('class');
    $("#tabHeader_" + tab_num).attr("class","tabActiveHeader");

    var table_changelist = $("#tabpage_" + tab_num + " > #changelist");

    if (table_changelist.length != 0 && tab_num != current_tab_id && 
	(typeof page_num == 'undefined' || page_num == tab_holder.attr('data-current-tab' + tab_num + '-page'))) {
	$("#tabpage_" + current_tab_id).hide();
	$("#tabpage_" + tab_num).show();
    } else if (table_changelist.length == 0 || page_num != current_page_id || tab_num != current_tab_id) {
	if (typeof page_num == 'undefined') {
	    page_num = 1;
	}

	$("#tabpage_" + current_tab_id).hide();
	$("#tabpage_" + tab_num).empty();
	$("#tabpage_" + tab_num).append('<table cellspacing="0" id="changelist"><tr><h2>Loading...</h2></tr></table>')
	$("#tabpage_" + tab_num).show();

	var longitude = $('#client_long').text();
	var latitude = $('#client_lat').text();
	//alert(longitude);

	var get_url = 'view.py?geobrowsertried=True&longitude=' + longitude + '&latitude=' + latitude + '&wh_format=ajax&access_token=';
	get_url += access_token + '&page=' + page_num + '&sort_by=' + sort_by;
	get_url += '&wh_q=' + wh_q;
	/*
	if (tab_num == 1) {
	    get_url += '&wh_q=recommend';
	} else if (tab_num == 2) {
	    get_url += '&wh_q=deal';
	}
	*/
	get_url += '&callback=?';

	//alert(get_url);
	$.ajax({url:get_url}).done( function(data) {
		//alert('ajax get success' + data);
		$("#tabpage_" + tab_num).empty();
		$("#tabpage_" + tab_num).append(data);
		//alert(data);
		// not showing info diagram when hover for iphone
		// also, deal not using info diagram
		if ( tab_num != 2) {
		    $.getScript("/lmedia/js/dynamic.js");
		}
	} );
    }

    tab_holder.attr("data-current-tab", tab_num);
    tab_holder.attr("data-current-tab" + tab_num + "-page", page_num);
    tab_holder.attr('data-current-sort', sort_by);
}
