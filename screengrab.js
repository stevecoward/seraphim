var page = require('webpage').create();
page.open('{{ url }}', function() {
  page.settings.userAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36';
  page.viewportSize = {width: 1280, height: 1024};
  page.render('output/{{ output_filename }}');
  phantom.exit();
});