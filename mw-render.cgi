#!/usr/bin/env ruby19
# encoding: UTF-8

require 'cgi'
require 'net/http'
require 'rexml/document'
require 'digest/sha1'

URL_TMPL = 'http://www.cinsk.org/wiki/Special:Export/'


cgi = CGI.new

puts "Cache-Control: no-cache\r\n"
puts "Content-type: text/html; charset=utf-8\r\n\r\n"

#puts `which ruby`
#puts "name = #{cgi['name']}"

url = URL_TMPL + cgi['name']

xml_data = Net::HTTP.get_response(URI.parse(url)).body

doc = REXML::Document.new(xml_data)

#puts doc

title = REXML::XPath.first(doc, "//page/title").text
$body = REXML::XPath.first(doc, "//page/revision/text").text

$body_alt = <<eos
* Start each line
* with an [[Wikipedia:asterisk|asterisk]] (*).
** More asterisks gives deeper
*** and deeper levels.
* Line breaks<br />don't break levels.
*** But jumping levels creates empty space.
Any other start ends the list.
eos

class WikiPage
  attr_accessor :toc, :heads, :body, :codestate, :list

  def initialize()
    @body = ""
    @toc = {}
    @heads = {}
    @textstate = { :state => :text, :lang => "", :code => "" }
    @list = []
  end

  def entity_encode!(s)
    s.gsub!(/&/, "&amp;")
    s.gsub!(/</, "&lt;")
    s.gsub!(/>/, "&gt;")
    s.gsub!(/"/, "&quot;")
    s
  end

  def flush()
    if @textstate[:code] != ""
      append '<pre class="prettyprint linenums">' +
        entity_encode!(@textstate[:code]) + "</pre>\n\n"
    end
    @textstate[:code] = ""
    @textstate[:lang] = ""
  end

  def append(s)
    #puts "APPEND: #{s}"
    @body += s
  end

  def parse_line_indented(line)
    if @textstate[:state] == :text
      @textstate[:state] = :pre
    end
    @textstate[:code] += line
  end

  def parse_line_source_begin(line)
    m = /lang *= *"([^"]*)"/.match line
    @textstate[:lang] = m[1] if m != nil

    case @textstate[:state]
    when :text
      @textstate[:state] = :source
    when :pre
      flush
      @textstate[:state] = :text
    when :source
      @textstate[:code] += line
    end
  end

  def parse_line_source_end(line)
    case @textstate[:state]
    when :source
      flush
      @textstate[:state] = :text
    else
      # huh???
      append line
    end
  end

  def parse(body)
    body.each_line { |line|
      if line =~ /^[ \t]/
        parse_line_indented line
      elsif line =~ /^<source/
        parse_line_source_begin line
      elsif line =~ /^<\/source>/
        parse_line_source_end line
      else
        case @textstate[:state]
        when :text
          append line
        when :pre
          flush
          @textstate[:state] = :text
          append line
        when :source
          @textstate[:code] += line
        end
      end
    }
    parse_headers
  end

  @@hdrs = [
    [ /^====== *(.+?) *====== *$/, "h6" ],
    [ /^===== *(.+?) *===== *$/, "h5" ],
    [ /^==== *(.+?) *==== *$/, "h4" ],
    [ /^=== *(.+?) *=== *$/, "h3" ] ];

  def parse_headers ()
    @@hdrs.each { |elem|
      @body.gsub!(elem[0]) { |mtext|
        hash = Digest::SHA1.hexdigest $1
        @heads[$1] = hash

        <<eos
  <#{elem[1]}><span id="#{hash}">#{$1}</span></#{elem[1]}>
eos
      }
    }

    first = true
    @body.gsub!(/^== *(.+?) *== *$/) { |mtext|
      hash = Digest::SHA1.hexdigest $1
      @toc[hash] = $1
      @heads[$1] = hash

      #puts "match: #{$1}"

      if ! first
        prefix = "</section>"
      else
        prefix = ""
        first = false
      end

      <<eos
        #{prefix}
        <section id="#{hash}">
          <div class="page-header">
            <h1>#{$1}</h1>
          </div>
eos
    }
    @body += "\n        </section>\n"

    @body.gsub!(/\[\[#([^|]+)\|(.+)\]\]/) { |mtext|
      if @heads[$1]
        <<eos
<a href="##{@heads[$1]}">#{$2}</a>
eos
      else
        mtext
      end
    }
  end

  def render_header
    puts <<eos
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <meta charset="utf-8"/>
    <title>Article: #{@title}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <meta name="description" content=""/>
    <meta name="author" content=""/>

    <!-- Le styles -->

    <link href="assets/css/bootstrap.css" rel="stylesheet"/>
    <link href="assets/css/bootstrap-responsive.css" rel="stylesheet"/>
    <link href="assets/css/docs.css" rel="stylesheet"/>
    <link href="assets/js/google-code-prettify/prettify.css" rel="stylesheet"/>

    <!-- Le HTML5 shim, for IE6-8 support of HTML5 elements -->
    <!--[if lt IE 9]>
      <script src="http://html5shim.googlecode.com/svn/trunk/html5.js"></script>
    <![endif]-->

    <!-- Le fav and touch icons -->
    <link rel="apple-touch-icon-precomposed" sizes="144x144" href="assets/ico/apple-touch-icon-144-precomposed.png"/>

    <link rel="apple-touch-icon-precomposed" sizes="114x114" href="assets/ico/apple-touch-icon-114-precomposed.png"/>
    <link rel="apple-touch-icon-precomposed" sizes="72x72" href="assets/ico/apple-touch-icon-72-precomposed.png"/>
    <link rel="apple-touch-icon-precomposed" href="assets/ico/apple-touch-icon-57-precomposed.png"/>
    <link rel="shortcut icon" href="assets/ico/favicon.png"/>

  </head>

  <body data-spy="scroll" data-target=".bs-docs-sidebar">

    <!-- Navbar
    ================================================== -->
    <div class="navbar navbar-inverse navbar-fixed-top">
      <div class="navbar-inner">
        <div class="container">
          <button type="button" class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>

          </button>
          <a class="brand" href="./index.html">Bootstrap</a>
          <div class="nav-collapse collapse">
            <ul class="nav">
              <li class="">
                <a href="./index.html">Home</a>
              </li>
              <li class="">

                <a href="./getting-started.html">Get started</a>
              </li>
              <li class="active">
                <a href="./scaffolding.html">Scaffolding</a>
              </li>
              <li class="">
                <a href="./base-css.html">Base CSS</a>

              </li>
              <li class="">
                <a href="./components.html">Components</a>
              </li>
              <li class="">
                <a href="./javascript.html">JavaScript</a>
              </li>
              <li class="">

                <a href="./customize.html">Customize</a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

<header class="jumbotron subhead" id="overview">
  <div class="container">
    <h1>#{@title}</h1>
    <p class="lead">description</p>
  </div>
</header>

  <div class="container">

    <!-- Docs nav
    ================================================== -->

    <div class="row">
      <div class="span3 bs-docs-sidebar">
        <ul class="nav nav-list bs-docs-sidenav">
eos
  end

  def render_footer
    puts <<eos

      </div>
    </div>

  </div>



    <!-- Footer
    ================================================== -->
    <footer class="footer">
      <div class="container">
        <p>Designed and built with all the love in the world by <a href="http://twitter.com/mdo" target="_blank">@mdo</a> and <a href="http://twitter.com/fat" target="_blank">@fat</a>.</p>

        <p>Code licensed under <a href="http://www.apache.org/licenses/LICENSE-2.0" target="_blank">Apache License v2.0</a>, documentation under <a href="http://creativecommons.org/licenses/by/3.0/">CC BY 3.0</a>.</p>
        <p><a href="http://glyphicons.com">Glyphicons Free</a> licensed under <a href="http://creativecommons.org/licenses/by/3.0/">CC BY 3.0</a>.</p>
        <ul class="footer-links">
          <li><a href="http://blog.getbootstrap.com">Blog</a></li>

          <li class="muted">&middot;</li>
          <li><a href="https://github.com/twitter/bootstrap/issues?state=open">Issues</a></li>
          <li class="muted">&middot;</li>
          <li><a href="https://github.com/twitter/bootstrap/wiki">Roadmap and changelog</a></li>
        </ul>
      </div>
    </footer>


    <!-- Le javascript
    ================================================== -->
    <!-- Placed at the end of the document so the pages load faster -->
    <script type="text/javascript" src="http://platform.twitter.com/widgets.js"></script>
    <script src="assets/js/jquery.js"></script>
    <script src="assets/js/bootstrap-transition.js"></script>
    <script src="assets/js/bootstrap-alert.js"></script>

    <script src="assets/js/bootstrap-modal.js"></script>
    <script src="assets/js/bootstrap-dropdown.js"></script>
    <script src="assets/js/bootstrap-scrollspy.js"></script>
    <script src="assets/js/bootstrap-tab.js"></script>
    <script src="assets/js/bootstrap-tooltip.js"></script>
    <script src="assets/js/bootstrap-popover.js"></script>

    <script src="assets/js/bootstrap-button.js"></script>
    <script src="assets/js/bootstrap-collapse.js"></script>
    <script src="assets/js/bootstrap-carousel.js"></script>
    <script src="assets/js/bootstrap-typeahead.js"></script>
    <script src="assets/js/bootstrap-affix.js"></script>

    <script src="assets/js/holder/holder.js"></script>

    <script src="assets/js/google-code-prettify/prettify.js"></script>

    <script src="assets/js/application.js"></script>
  </body>
</html>
eos
  end

  def render
    render_header

    @toc.each_pair { |id, title|
      puts <<eos
          <li><a href="##{id}"><i class="icon-chevron-right"></i>
              #{title}</a></li>
eos
    }
    puts <<eos
        </ul>
      </div>
    <div class="span9">
eos
    puts @body

    render_footer
  end

end

page = WikiPage.new()
page.parse($body)
page.render

exit 0
#puts "title: #{title}"
#puts "body: #{$body}"

$toc = {}                        # key: hash, value: title
$head_links = {}                 # key: title, value: hash

$new_body = ""
$code_queue = ""
$current_obj = :text;
$code_lang = ""
$list_depth = 0
$list_type = nil

def encode_entity!(s)
  #return s
  s.gsub!(/&/, "&amp;")
  s.gsub!(/</, "&lt;")
  s.gsub!(/>/, "&gt;")
  s.gsub!(/"/, "&quot;")
  s
end

def flush_code!()
  if $code_queue != ""
    $new_body += '<pre class="prettyprint linenums">' +
      encode_entity!($code_queue) + "</pre>\n\n"
  end
  $code_queue = ""
  $code_lang = ""
end

def append_text(s)
  #puts "APPEND: #{s}"
  $new_body += s
end

$body.each_line { |line|
  if line =~ /^[ \t]/
    case $current_obj
    when :text
      $current_obj = :pre
      #STDERR.write("PRE: #{line}\n")
      #code_queue += "<!-- PRE: #{line} -->\n"
      $code_queue += line
    when :pre
      $code_queue += line
    when :source
      $code_queue += line
    end
  elsif line =~ /^<source/
    m = /lang *= *"([^"]*)"/.match line
    $code_lang = m[1] if m != nil

    case $current_obj
    when :text
      $current_obj = :source
    when :pre
      flush_code!
      $current_obj = :text
    when :source
      $code_queue += line
    end
  elsif line =~ /^<\/source>/
    case $current_obj
    when :source
      flush_code!
      $current_obj = :text
    else
      # huh???
      $new_body += line
    end
  else
    case $current_obj
    when :text
      case line
      when /^(\*+) +(.*)$/
        #puts "LIST[#{$1}]: |#{$2}|"
        l_depth = $1.length
        l_type = :ul
        #puts "list_type: old(#{$list_type}) now(#{l_type})"
        #append_text "LIST_DEPTH: OLD(#{$list_depth}) NOW(#{l_depth})\n"

        if $list_type == nil
          # new list start now.
          $list_type = l_type
          $list_depth = l_depth
          append_text " " * l_depth + "<ul>\n" +
            " " * l_depth + "<li>#{$2}</li>\n"
        elsif l_type == $list_type
          if l_depth == $list_depth
            # just add another item
            append_text " " * l_depth + "<li>#{$2}</li>\n"
          elsif l_depth > $list_depth
            # enter another list group
            (0...(l_depth - $list_depth)).each { |i|
              append_text " " * ($list_depth + i + 1) + "<ul>\n"
            }
            append_text " " * l_depth + "<li>#{$2}</li>\n"
            $list_depth = l_depth
          else # l_depth < list_depth
            #append_text "LEAVE\n"
            # leave previous group
            (0...($list_depth - l_depth)).each { |i|
              append_text " " * ($list_depth - i) + "</ul>\n"
            }
            append_text " " * l_depth + "<li>#{$2}</li>\n"
            $list_depth = l_depth
          end
        else
          # different type of list starts
        end
      when /^(\#+) +/
        l_depth = $1.length
        l_type = :ol
      else
        $list_type = nil
        $list_depth = 0

        $new_body += line
        end

    when :pre
      flush_code!
      $current_obj = :text

      $new_body += line
    when :source
      $code_queue += line
    end
  end
  #puts "[#{$current_obj}] [#{line[0].ord}] |#{line}|"
}

$new_body += $code_queue if $code_queue != ""

$body = $new_body

#puts $body
#puts "hello"
#exit(0)


$body.gsub!(/^====== *(.+?) *====== *$/) { |match|
  hash = Digest::SHA1.hexdigest $1
  $head_links[$1] = hash

  <<eos
  <h6><span id="#{hash}">#{$1}</span></h6>
eos
}
$body.gsub!(/^===== *(.+?) *===== *$/) { |match|
  hash = Digest::SHA1.hexdigest $1
  $head_links[$1] = hash

  <<eos
  <h5><span id="#{hash}">#{$1}</span></h5>
eos
}
$body.gsub!(/^==== *(.+?) *==== *$/) { |match|
  hash = Digest::SHA1.hexdigest $1
  $head_links[$1] = hash

  <<eos
  <h4><span id="#{hash}">#{$1}</span></h4>
eos
}
$body.gsub!(/^=== *(.+?) *=== *$/) { |match|
  hash = Digest::SHA1.hexdigest $1
  $head_links[$1] = hash

  <<eos
  <h3><span id="#{hash}">#{$1}</span></h3>
eos

}

first_section = true

$body.gsub!(/^== *(.+?) *== *$/) { |match|
  hash = Digest::SHA1.hexdigest $1
  $toc[hash] = $1
  $head_links[$1] = hash

  #puts "match: #{$1}"

  if ! first_section
    prefix = "</section>"
  else
    prefix = ""
    first_section = false
  end

  <<eos
        #{prefix}
        <section id="#{hash}">
          <div class="page-header">
            <h1>#{$1}</h1>
          </div>
eos
}
$body += "\n        </section>\n"


$body.gsub!(/\[\[#([^|]+)\|(.+)\]\]/) { |match|
  if $head_links[$1]
    <<eos
<a href="##{$head_links[$1]}">#{$2}</a>
eos
  else
    match
  end
}


puts <<eos
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <meta charset="utf-8"/>
    <title>Article: #{$title}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <meta name="description" content=""/>
    <meta name="author" content=""/>

    <!-- Le styles -->

    <link href="assets/css/bootstrap.css" rel="stylesheet"/>
    <link href="assets/css/bootstrap-responsive.css" rel="stylesheet"/>
    <link href="assets/css/docs.css" rel="stylesheet"/>
    <link href="assets/js/google-code-prettify/prettify.css" rel="stylesheet"/>

    <!-- Le HTML5 shim, for IE6-8 support of HTML5 elements -->
    <!--[if lt IE 9]>
      <script src="http://html5shim.googlecode.com/svn/trunk/html5.js"></script>
    <![endif]-->

    <!-- Le fav and touch icons -->
    <link rel="apple-touch-icon-precomposed" sizes="144x144" href="assets/ico/apple-touch-icon-144-precomposed.png"/>

    <link rel="apple-touch-icon-precomposed" sizes="114x114" href="assets/ico/apple-touch-icon-114-precomposed.png"/>
    <link rel="apple-touch-icon-precomposed" sizes="72x72" href="assets/ico/apple-touch-icon-72-precomposed.png"/>
    <link rel="apple-touch-icon-precomposed" href="assets/ico/apple-touch-icon-57-precomposed.png"/>
    <link rel="shortcut icon" href="assets/ico/favicon.png"/>

  </head>

  <body data-spy="scroll" data-target=".bs-docs-sidebar">

    <!-- Navbar
    ================================================== -->
    <div class="navbar navbar-inverse navbar-fixed-top">
      <div class="navbar-inner">
        <div class="container">
          <button type="button" class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>

          </button>
          <a class="brand" href="./index.html">Bootstrap</a>
          <div class="nav-collapse collapse">
            <ul class="nav">
              <li class="">
                <a href="./index.html">Home</a>
              </li>
              <li class="">

                <a href="./getting-started.html">Get started</a>
              </li>
              <li class="active">
                <a href="./scaffolding.html">Scaffolding</a>
              </li>
              <li class="">
                <a href="./base-css.html">Base CSS</a>

              </li>
              <li class="">
                <a href="./components.html">Components</a>
              </li>
              <li class="">
                <a href="./javascript.html">JavaScript</a>
              </li>
              <li class="">

                <a href="./customize.html">Customize</a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

<header class="jumbotron subhead" id="overview">
  <div class="container">
    <h1>#{$title}</h1>
    <p class="lead">description</p>
  </div>
</header>

  <div class="container">

    <!-- Docs nav
    ================================================== -->

    <div class="row">
      <div class="span3 bs-docs-sidebar">
        <ul class="nav nav-list bs-docs-sidenav">
eos

$toc.each_pair { |k, v|
  #puts "#{k} = #{v}"
  puts <<eos
          <li><a href="##{k}"><i class="icon-chevron-right"></i>#{v}</a></li>
eos
}

puts <<eos
        </ul>
      </div>
    <div class="span9">
eos

puts $body

puts <<eos

      </div>
    </div>

  </div>



    <!-- Footer
    ================================================== -->
    <footer class="footer">
      <div class="container">
        <p>Designed and built with all the love in the world by <a href="http://twitter.com/mdo" target="_blank">@mdo</a> and <a href="http://twitter.com/fat" target="_blank">@fat</a>.</p>

        <p>Code licensed under <a href="http://www.apache.org/licenses/LICENSE-2.0" target="_blank">Apache License v2.0</a>, documentation under <a href="http://creativecommons.org/licenses/by/3.0/">CC BY 3.0</a>.</p>
        <p><a href="http://glyphicons.com">Glyphicons Free</a> licensed under <a href="http://creativecommons.org/licenses/by/3.0/">CC BY 3.0</a>.</p>
        <ul class="footer-links">
          <li><a href="http://blog.getbootstrap.com">Blog</a></li>

          <li class="muted">&middot;</li>
          <li><a href="https://github.com/twitter/bootstrap/issues?state=open">Issues</a></li>
          <li class="muted">&middot;</li>
          <li><a href="https://github.com/twitter/bootstrap/wiki">Roadmap and changelog</a></li>
        </ul>
      </div>
    </footer>


    <!-- Le javascript
    ================================================== -->
    <!-- Placed at the end of the document so the pages load faster -->
    <script type="text/javascript" src="http://platform.twitter.com/widgets.js"></script>
    <script src="assets/js/jquery.js"></script>
    <script src="assets/js/bootstrap-transition.js"></script>
    <script src="assets/js/bootstrap-alert.js"></script>

    <script src="assets/js/bootstrap-modal.js"></script>
    <script src="assets/js/bootstrap-dropdown.js"></script>
    <script src="assets/js/bootstrap-scrollspy.js"></script>
    <script src="assets/js/bootstrap-tab.js"></script>
    <script src="assets/js/bootstrap-tooltip.js"></script>
    <script src="assets/js/bootstrap-popover.js"></script>

    <script src="assets/js/bootstrap-button.js"></script>
    <script src="assets/js/bootstrap-collapse.js"></script>
    <script src="assets/js/bootstrap-carousel.js"></script>
    <script src="assets/js/bootstrap-typeahead.js"></script>
    <script src="assets/js/bootstrap-affix.js"></script>

    <script src="assets/js/holder/holder.js"></script>

    <script src="assets/js/google-code-prettify/prettify.js"></script>

    <script src="assets/js/application.js"></script>
  </body>
</html>
eos

# Local Variables:
# mode: ruby
# End: