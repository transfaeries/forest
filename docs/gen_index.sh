#!/bin/bash
function create_gnu_index ()
{
    # call it right or die
    [[ $# != 3 ]] && echo "bad args. do: $FUNCNAME '/DOCUMENT_ROOT/' '/' 'gnu.askapache.com'" && exit 2

    # D is the doc_root containing the site
    local L= D="$1" SUBDIR="$2" DOMAIN="$3" F=

    # if dir doesnt exist, create it
    [[ -d $D ]] || mkdir -p $D;

    # cd into dir or die
    cd $D || exit 2;

    # remove empty directories, they dont need to be there and slow things down if they are
    find . -maxdepth 1 -type d -empty -exec rm -rf {} \;

    # start of total output for saving as index.html
    (

        # print the html header
        echo '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">';
        echo "<html><head><title>Index of http://${DOMAIN}${SUBDIR}</title></head>";
        echo "<body><h1 id="Index_SUBDIR">Index of ${SUBDIR} <a class="sl" href="#Index_SUBDIR"></a></h1><pre>      Name                                        Last modified      Size";

        # start of content output
        (
            # change IFS locally within subshell so the for loop saves line correctly to L var
            IFS=$'\n';

            # pretty sweet, will mimick the normal apache output
            for L in $(find -L . -mount -depth -maxdepth 1 -type f ! -name 'index.html' -printf "      <a href=\"%f\">%-44f@_@%Td-%Tb-%TY %Tk:%TM  @%f@\n"|sort|sed 's,\([\ ]\+\)@_@,</a>\1,g');
            do
                # file
                F=$(sed -e 's,^.*@\([^@]\+\)@.*$,\1,g'<<<"$L");

                # file with file size
                F=$(du -bh $F | cut -f1);

                # output with correct format
                sed -e 's,\ @.*$, '"$F"',g'<<<"$L";
            done;
        )

        # now output a list of all directories in this dir (maxdepth 1) other than '.' outputting in a sorted manner exactly like apache
        find -L . -mount -depth -maxdepth 1 -type d ! -name '.' -printf "      <a href=\"%f\">%-43f@_@%Td-%Tb-%TY %Tk:%TM  -\n"|sort -d|sed 's,\([\ ]\+\)@_@,/</a>\1,g'

        # print the footer html
        echo "</pre><address>Apache Server at ${DOMAIN}</address></body></html>";

    # finally save the output of the subshell to index.html
    );

}

create_gnu_index $PWD/docs/ /forest-draft/ forestcontact.github.io
