$(document).ready(function(){
	var elem_name = $('#main').attr('data-name');
	$('#'+elem_name).addClass('checked');

	$('.ul-name-list li').on('click', function() {
		$('.ul-name-list .checked').removeClass('checked');
		$(this).addClass('checked');
	});
	$('.ul-menu li').on('click', function() {
		$('.ul-menu .checked').removeClass('checked');
		$(this).addClass('checked');
	});

	var rel_height = $(window).height();
	$('.wrap-paper').style = 'height:' + rel_height+'px';
});