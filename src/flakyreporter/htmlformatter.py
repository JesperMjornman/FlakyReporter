import os
from shutil import rmtree

class HtmlFormatter(object):
    def _init_workspace(args_reset, func_name):
        if 'reports' not in os.listdir():
            os.mkdir('reports')

        if args_reset:
            try:
                rmtree(('./reports/{}').format(func_name))
            except Exception as e:
                print(e)
        try:
            os.mkdir(('./reports/{}/').format(func_name))
            os.mkdir(('./reports/{}/locals').format(func_name))
            os.mkdir(('./reports/{}/returns').format(func_name))
        except Exception as e:
            pass

    def button_render(content):
        try:
            if len(content) > 0:
                return True
            else:
                return False
        except:
            print("Optional button render failed.")

    def format_assertion(text, assertion_str = None):
        if assertion_str is not None:
            assertion_str = '<b>' + assertion_str + '</b><BR><BR>'
        else:
            assertion_str = ''

        text = text.replace(".\n", ".\n<BR>")
        if '.\n' in text:
            text = text.replace(".\n", "<SPAN style='font-size:12px;'>&#10071</SPAN>\n", 1)
        return assertion_str + text
    
    def format_html_locals(text):
        try:
            func_name = text.split('\"')[1]
            #bind_readmore = "<a href=\"./data/locals/{}.html\">read more</a>".format(func_name)
        except:
            raise
        return ""

    def format_to_html(text, data_type = None): 
        try:
            text = text.replace(".\n", ".\n<BR>")
            if ' passed iterations.\n' in text and data_type != None:
                text = text.replace("passed iterations.\n", "passed iterations. <SPAN id='new' style='color:green;'>(&#10003)</SPAN><a href=javascript:render_detailed();> read more</a>")
            if ' passed iterations.\n' in text and data_type == None:
                text = text.replace("passed iterations.\n", "passed iterations. <SPAN style='color:green;'>(&#10003)</SPAN>")

            if ' failed iterations.\n' in text and data_type != None:
                text = text.replace("failed iterations.\n", "failed iterations. <SPAN style='color:red;'>(&#10008)</SPAN><a href=javascript:render_detailed();> read more</a>")
            if ' failed iterations.\n' in text and data_type == None:
                text = text.replace("failed iterations.\n", "failed iterations. <SPAN style='color:green;'>(&#10003)</SPAN>")
        except:
            print("Failed to format HTML.")
        return text

    def format_system_meta(meta):
        try:
            return (
                          ("<P1>Platform:  {}</P1><BR>".format(meta['OS']['platform']))
                        + ("<P1>System:    {}</P1><BR>".format(meta['OS']['system']))
                        + ("<P1>Release:   {}</P1><BR>".format(meta['OS']['release']))
                        + ("<P1>Version:   {}</P1><BR>".format(meta['OS']['version']))
                        + ("<P1>Machine:   {}</P1><BR>".format(meta['OS']['machine']))
                        + ("<P1>Processor: {}</P1><BR>".format(meta['OS']['processor']))
                        + ("<P1>Pyversion: {}</P1><BR>".format(meta['OS']['pyversion']))
                        + ("<P1>Date:      {}</P1><BR><BR>".format(meta['DATE'])))
        except:
            print("Failed to fetch System Meta.")

    def determine_probability(probability): 
        if probability >= 0.0 and probability <= 0.1:
            result = "has <P1 style='color:green; font-weight:bold;'>no indications of Randomness</P1>"
        elif probability > 0.1 and probability <= 0.4:
            result = "has <P1 style='color:green; font-weight:bold;'>few indications of Randomness</P1>"
        elif probability > 0.4 and probability <= 0.7:
            result = "has <P1 style='color:orange; font-weight:bold;'>some indications of Randomness</P1>"
        elif probability > 0.7:
            result = "has <P1 style='color:red; font-weight:bold;'>many indications of Randomness</P1>"
        try:
            return (("{} <P1>based on the collected information below.</P1><BR>").format(result))
        except:
            print("Failed to fetch probability.")
    
    @staticmethod
    def create_html(collected_information, probability, meta, iterations, args_reset):
        B_HEADER   = (    ("<!DOCTYPE html><HTML LANG='EN'>")
                        + ("<HEAD>")
                        + ("<TITLE> FlakyReport </TITLE><H1 style='text-align:center; text-decoration:underline;'>FlakyReport</H1>")
                        + ("<LINK rel='stylesheet' href='https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css'>")
                        + ("<SCRIPT src='https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js'></SCRIPT>")
                        + ("<SCRIPT src='https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/js/bootstrap.min.js'></SCRIPT>")
                        + ("<SCRIPT>function render_detailed() { \
                            \
                            document.body.innerHTML = 'Refresh to return.' \
                            } \
                           </SCRIPT>")
                        + ("</HEAD>")
                        + ("<BODY style='background-color: rgb(230, 230, 230)'>")
                        + ("<DIV style='position:relative; left:0.5%;'>"))
                        
        ITERATIONS = (    ("<H2 style='left:0.5%; position:relative;'>Number of Iterations:</H2>")
                        + ("<DIV style='left:0.5%; position:relative; background-color:lightgrey; border:solid black 1px; width:98%;' contenteditable='false'>")
                        + ("<BR><P style='left:0.5%; position:relative; font-size:16px;'> PASSED <SPAN style='color:green;'>(&#10003)</SPAN>: {}</P>").format(iterations['passed'])
                        + ("<P style='left:0.5%; position:relative; font-size:16px;'> FAILED &nbsp&nbsp<SPAN style='color:red;'>(&#10008)</SPAN>: {}</P></DIV>").format(iterations['failed']))

        RESULT     = (    ("<H2 style='left:0.5%; position:relative;'>Result:</H2><DIV style='left:0.5%; position:relative; background-color:lightgrey; border:solid black 1px; width:98%;'><P1 style='position:relative; left:0.5%; font-size:18px;' contenteditable='false'><P1><BR>The function {}{}{}</P1> {}<BR>")
                            .format('&#10078', HtmlFormatter.format_to_html(collected_information['func_name']), '&#10078', HtmlFormatter.determine_probability(probability)))

        LOCALS     = (    ("<BUTTON type='button' class='btn btn-info' data-toggle='collapse' data-target='#Locals' style='position:relative; width:120px; height:50px; border:none; background-color:black; font-size:large;'>Locals: </BUTTON><BR>")
                        + ("<DIV id='Locals' class='collapse'><BR>")
                        + ("<DIV style='left:0.5%; position:relative; background-color:lightgrey; border:solid black 1px; width:98%;' contenteditable='false'>")
                        + ("<BR><DIV style='left:0.5%; position:relative;'>{}</DIV><BR></DIV></DIV><BR>").format(HtmlFormatter.format_to_html(collected_information['locals'], data_type='locals')))

        ASSERTIONS = (    ("<BUTTON type='button' class='btn btn-info' data-toggle='collapse' data-target='#Assertions' style='position:relative; width:120px; height:50px; border:none; background-color:black; font-size:large;'>Assertions: </BUTTON><BR>")
                        + ("<DIV id='Assertions' class='collapse'><BR>")
                        + ("<DIV style='left:0.5%; position:relative; background-color:lightgrey; border:solid black 1px; width:98%;' contenteditable='false'>")
                        + ("<BR><DIV style='left:0.5%; position:relative;'>{}</DIV><BR></DIV></DIV><BR>").format(HtmlFormatter.format_assertion(collected_information['assertions'], collected_information['assert_str'])))
        
        RETURNS    = (    ("<BUTTON type='button' class='btn btn-info' data-toggle='collapse' data-target='#Returns' style='position:relative; width:120px; height:50px; border:none; background-color:black; font-size:large;'>Returns: </BUTTON><BR>")
                        + ("<DIV id='Returns' class='collapse'><BR>")
                        + ("<DIV style='left:0.5%; position:relative; background-color:lightgrey; border:solid black 1px; width:98%;' contenteditable='false'>")
                        + ("<BR><DIV style='left:0.5%; position:relative;'>{}</DIV><BR></DIV></DIV><BR>").format(HtmlFormatter.format_to_html(collected_information['returns'], data_type='returns')))

        KEYWORDS   = (    ("<BUTTON type='button' class='btn btn-info' data-toggle='collapse' data-target='#Keywords' style='position:relative; width:120px; height:50px; border:none; background-color:black; font-size:large;'>Keywords: </BUTTON><BR>")
                        + ("<DIV id='Keywords' class='collapse'><BR>")
                        + ("<DIV style='left:0.5%; position:relative; background-color:lightgrey; border:solid black 1px; width:98%;' contenteditable='false'>")
                        + ("<BR><DIV style='left:0.5%; position:relative;'>{}</DIV><BR></DIV></DIV><BR>").format(HtmlFormatter.format_to_html(collected_information['keywords'])))
        # Fixa formattering på divergence.
        DIVERGENCE = (    ("<BUTTON type='button' class='btn btn-info' data-toggle='collapse' data-target='#Divergence' style='position:relative; width:120px; height:50px; border:none; background-color:black; font-size:large;'>Divergence: </BUTTON><BR>")
                        + ("<DIV id='Divergence' class='collapse'><BR>")
                        + ("<DIV style='left:0.5%; position:relative; background-color:lightgrey; border:solid black 1px; width:98%;' contenteditable='false'>")
                        + ("<BR><DIV style='left:0.5%; position:relative;'>{}</DIV><BR></DIV></DIV><BR>").format(HtmlFormatter.format_to_html(collected_information['divergence'])))#, HtmlFormatter.format_to_html(collected_information['commons'])))

        B_DIVIDER  = (    ("</P1></DIV><BR><H2 style='left:0.5%; position:relative;'>Additional Information:</H2><DIV style='left:0.5%; position:relative; background-color:lightgrey; border:solid black 1px; width:98%;' contenteditable='false'><BR>"))

        META       = (    ("<BUTTON type='button' class='btn btn-info' data-toggle='collapse' data-target='#META' style='position:relative; width:120px; height:50px; left:0.5%; border:none; background-color:black; font-size:large;'>Meta: </BUTTON><BR>")
                        + ("<DIV id='META' class='collapse' style='left:0.5%; position:relative;'><BR>")
                        + ("<DIV style='left:0.5%; position:relative; background-color:lightgrey; border:solid black 1px; width:98%;' contenteditable='false'>")
                        + ("<BR><DIV style='left:0.5%; position:relative; font-size:18px;'>{}</DIV></DIV></DIV>").format(HtmlFormatter.format_system_meta(meta)))

        E_DIVIDER  = (    ("<BR></DIV>"))

        E_HEADER   = (    ("</BODY></HTML></DIV>"))

        try:
            HtmlFormatter._init_workspace(args_reset, collected_information['func_name'])
            with open('./reports/'+collected_information['func_name']+'/report.html', "w") as file:
                try:
                    file.write(B_HEADER)
                    if HtmlFormatter.button_render(iterations):
                        file.write(ITERATIONS)
                    file.write(RESULT)
                except:
                    print("Exited report.html unexpectedly.")
                    return

                try:
                    if HtmlFormatter.button_render(collected_information['locals']):    
                        file.write(LOCALS)
                    if HtmlFormatter.button_render(collected_information['assertions']):
                        file.write(ASSERTIONS)
                    if HtmlFormatter.button_render(collected_information['returns']):
                        file.write(RETURNS)
                    if HtmlFormatter.button_render(collected_information['keywords']):
                        file.write(KEYWORDS)
                    if HtmlFormatter.button_render(collected_information['divergence']) or HtmlFormatter.button_render(collected_information['commons']):
                        file.write(DIVERGENCE)

                    try:
                        file.write(B_DIVIDER)
                    except:
                        print("Exited report.html unexpectedly.")

                    if HtmlFormatter.button_render(meta):
                        file.write(META)

                    try:
                        file.write(E_DIVIDER)
                    except:
                        print("Exited report.html unexpectedly.")

                except:
                    print("Failed when writing to report.html.")
                    return
                    
                try:
                    file.write(E_HEADER)
                except:
                    print("Exited report.html unexpectedly.")
                    return

                print("\nCreated report.html for: {}".format(collected_information['func_name']))
        except Exception as e:
            print("Failed to create report.html for: {}".format(collected_information['func_name']))
