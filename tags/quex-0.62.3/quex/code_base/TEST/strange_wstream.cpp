#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#include <quex/code_base/test_environment/StrangeStream>
#include <sstream>
#include <iostream>
#include <cstdlib>
#include <cstring>

int
main(int argc, char** argv)
{
    using namespace std;
    using namespace quex;

    if( argc < 2 ) {
        cout << "Error: require one command line argument.\n";
        return 0;
    }
    if( strcmp(argv[1], "--hwut-info") == 0 ) {
        cout << "StrangeStream: wchar_t stream based.;\n";
        cout << "CHOICES:  2, 3, 4, 5;\n";
        return 0;
    }
    const int Delta = atoi(argv[1]);

    wchar_t          buffer[1024];
    wstringstream    sh;
    long             position_list[6];

    sh << L"Im Fruetau zu Berge wir ziehen.";
    sh.seekg(0);

    StrangeStream<wstringstream> ssh(&sh);

    for(int i=0; i<6; ++i) {
        cout << "position: " << ssh.tellg() << endl;
        position_list[i] = ssh.tellg();
        ssh.read(buffer, Delta);
        buffer[ssh.gcount()] = '\0';
        cout << "content:  <";
        wcout << buffer;
        cout << ">" << endl;
    }
    cout << "Re-Do ---------------------------------------------\n";
    for(int i=0; i<6; ++i) {
        ssh.seekg(position_list[i]);
        cout << "position: " << ssh.tellg() << endl;
        ssh.read(buffer, Delta);
        buffer[ssh.gcount()] = L'\0';
        cout << "content:  <";
        wcout << buffer;
        cout << ">" << endl;
    }
}


