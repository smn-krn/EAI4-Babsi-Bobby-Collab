#include <iostream>
#include <fstream>

int main() {
        std::ofstream file("output.txt", std::ios::app);

        file << "Hello to my file." << std::endl;

        //std::ifstream


        std::cout << "Finished" << std::endl;
        return 0;
}
