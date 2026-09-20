// Maxx JNI bridge - Level 1 bootstrap interpreter
//
// This is a minimal embedded Maxx interpreter for Android.
// It recognizes a subset of Maxx syntax:
//   - io.println("...")
//   - let x = value
//   - Basic arithmetic on numbers
//   - str(value) conversion
//
// The production Maxx runtime (Level 2+) will replace this with
// the full AOT-compiled runtime.

#include <jni.h>
#include <string>
#include <sstream>
#include <map>
#include <cmath>
#include <cstdlib>

static std::map<std::string, double> variables;

static std::string trim(const std::string& s) {
    size_t start = s.find_first_not_of(" \t\r\n");
    if (start == std::string::npos) return "";
    size_t end = s.find_last_not_of(" \t\r\n");
    return s.substr(start, end - start + 1);
}

static double eval_expr(const std::string& expr) {
    std::string e = trim(expr);
    if (e.empty()) return 0.0;

    // Try number literal.
    char* end;
    double val = strtod(e.c_str(), &end);
    if (*end == '\0') return val;

    // Try variable lookup.
    auto it = variables.find(e);
    if (it != variables.end()) return it->second;

    // Handle function calls like sqrt(x), str(x).
    size_t paren = e.find('(');
    if (paren != std::string::npos && e.back() == ')') {
        std::string fn = e.substr(0, paren);
        std::string arg = e.substr(paren + 1, e.size() - paren - 2);
        double av = eval_expr(arg);
        if (fn == "sqrt") return sqrt(av);
        if (fn == "abs") return fabs(av);
        if (fn == "floor") return floor(av);
        if (fn == "ceil") return ceil(av);
        if (fn == "str" || fn == "int" || fn == "f64") return av;
    }

    // Handle binary ops: +, -, *, /, ^
    // Simple left-to-right evaluation for bootstrap.
    for (const char* op : {"+", "-", "*", "/", "^"}) {
        size_t pos = e.rfind(op);
        if (pos != std::string::npos && pos > 0) {
            // Skip if it's part of a number (like negative sign).
            if (op[0] == '-' && pos == 0) continue;
            std::string lhs = e.substr(0, pos);
            std::string rhs = e.substr(pos + 1);
            double lv = eval_expr(lhs);
            double rv = eval_expr(rhs);
            switch (op[0]) {
                case '+': return lv + rv;
                case '-': return lv - rv;
                case '*': return lv * rv;
                case '/': return lv / rv;
                case '^': return pow(lv, rv);
            }
        }
    }

    return 0.0;
}

static std::string eval_maxx(const std::string& code) {
    std::ostringstream out;
    std::istringstream iss(code);
    std::string line;

    while (std::getline(iss, line)) {
        line = trim(line);
        if (line.empty() || line[0] == '#') continue;

        // Skip function definition lines.
        if (line.substr(0, 1) == "@") continue;
        if (line == "ret 0" || line.substr(0, 4) == "ret ") continue;

        // io.println("...") or io.println(expr)
        if (line.find("io.println") != std::string::npos) {
            size_t start = line.find('(');
            size_t end = line.rfind(')');
            if (start != std::string::npos && end != std::string::npos) {
                std::string arg = line.substr(start + 1, end - start - 1);
                arg = trim(arg);

                // String literal.
                if (!arg.empty() && arg[0] == '"') {
                    size_t qend = arg.find('"', 1);
                    if (qend != std::string::npos) {
                        out << arg.substr(1, qend - 1) << "\n";
                        continue;
                    }
                }

                // String concatenation with +.
                if (arg.find("+") != std::string::npos) {
                    std::istringstream ss(arg);
                    std::string part;
                    while (std::getline(ss, part, '+')) {
                        part = trim(part);
                        if (!part.empty() && part[0] == '"') {
                            size_t qend = part.find('"', 1);
                            if (qend != std::string::npos) {
                                out << part.substr(1, qend - 1);
                            }
                        } else {
                            double v = eval_expr(part);
                            out << (long long)v;
                        }
                    }
                    out << "\n";
                    continue;
                }

                // Plain expression.
                double v = eval_expr(arg);
                // Print as int if it's whole number.
                if (v == floor(v) && fabs(v) < 1e15) {
                    out << (long long)v << "\n";
                } else {
                    out << v << "\n";
                }
            }
            continue;
        }

        // let x = value
        if (line.substr(0, 4) == "let ") {
            size_t eq = line.find('=');
            if (eq != std::string::npos) {
                std::string name = trim(line.substr(4, eq - 4));
                std::string val = line.substr(eq + 1);
                variables[name] = eval_expr(val);
            }
            continue;
        }

        // var x = value (same as let for bootstrap)
        if (line.substr(0, 4) == "var ") {
            size_t eq = line.find('=');
            if (eq != std::string::npos) {
                std::string name = trim(line.substr(4, eq - 4));
                std::string val = line.substr(eq + 1);
                variables[name] = eval_expr(val);
            }
            continue;
        }

        // x += value
        size_t plus_eq = line.find("+=");
        if (plus_eq != std::string::npos) {
            std::string name = trim(line.substr(0, plus_eq));
            std::string val = line.substr(plus_eq + 2);
            variables[name] += eval_expr(val);
            continue;
        }

        // x -= value
        size_t minus_eq = line.find("-=");
        if (minus_eq != std::string::npos) {
            std::string name = trim(line.substr(0, minus_eq));
            std::string val = line.substr(minus_eq + 2);
            variables[name] -= eval_expr(val);
            continue;
        }
    }

    return out.str();
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_maxx_app_MainActivity_runMaxx(
        JNIEnv* env,
        jobject /* this */,
        jstring code) {
    const char* code_str = env->GetStringUTFChars(code, nullptr);
    std::string result = eval_maxx(code_str);
    env->ReleaseStringUTFChars(code, code_str);
    return env->NewStringUTF(result.c_str());
}
