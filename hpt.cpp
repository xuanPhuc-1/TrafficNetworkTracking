#include <iostream>
using namespace std;

int main() {
    double a11, a12, a21, a22, b1, b2;

    // Nhập các hệ số của hệ phương trình
    cout << "Nhap cac he so cua he phuong trinh 2x2:" << endl;
    cout << "a11 = ";
    cin >> a11;
    cout << "a12 = ";
    cin >> a12;
    cout << "a21 = ";
    cin >> a21;
    cout << "a22 = ";
    cin >> a22;
    cout << "b1 = ";
    cin >> b1;
    cout << "b2 = ";
    cin >> b2;

    // Tính định thức của ma trận hệ số
    double det = a11*a22 - a12*a21;

    // Nếu định thức bằng 0, hệ phương trình vô nghiệm hoặc vô số nghiệm
    if (det == 0) {
        if (b1/a11 == b2/a21) {
            cout << "He phuong trinh co vo so nghiem." << endl;
        } else {
            cout << "He phuong trinh vo nghiem." << endl;
        }
    } else {
        // Tính nghiệm của hệ phương trình
        double x1 = (a22*b1 - a12*b2)/det;
        double x2 = (a11*b2 - a21*b1)/det;

        // In ra nghiệm của hệ phương trình
        cout << "Nghiem cua he phuong trinh la:" << endl;
        cout << "x1 = " << x1 << endl;
        cout << "x2 = " << x2 << endl;
    }

    return 0;
}
