#include <iostream>
#include <cmath>
using namespace std;

int main() {
    double a, b, c;
    double x1, x2;

    // Nhập các hệ số của phương trình bậc 2
    cout << "Nhap cac he so cua phuong trinh bac 2:" << endl;
    cout << "a = ";
    cin >> a;
    cout << "b = ";
    cin >> b;
    cout << "c = ";
    cin >> c;

    // Tính delta
    double delta = b*b - 4*a*c;

    // Kiểm tra giá trị của delta
    if (delta < 0) {
        cout << "Phuong trinh vo nghiem." << endl;
    } else if (delta == 0) {
        x1 = x2 = -b / (2*a);
        cout << "Phuong trinh co nghiem kep x1 = x2 = " << x1 << endl;
    } else {
        x1 = (-b + sqrt(delta)) / (2*a);
        x2 = (-b - sqrt(delta)) / (2*a);
        cout << "Phuong trinh co hai nghiem phan biet:" << endl;
        cout << "x1 = " << x1 << endl;
        cout << "x2 = " << x2 << endl;
    }

    return 0;
}
