#pragma once

#include <chrono>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iostream>
#include <nlohmann/json.hpp>
#include <opencv2/opencv.hpp>
#include <string>
#include <vector>

// Qt system setup
#ifdef QAPPLICATION_H
inline void QtSetup()
{
    qputenv("QT_STYLE_OVERRIDE", "");

    if (!qEnvironmentVariableIsSet("QT_DEVICE_PIXEL_RATIO") &&
        !qEnvironmentVariableIsSet("QT_AUTO_SCREEN_SCALE_FACTOR") &&
        !qEnvironmentVariableIsSet("QT_SCALE_FACTOR") &&
        !qEnvironmentVariableIsSet("QT_SCREEN_SCALE_FACTORS"))
    {
        QCoreApplication::setAttribute(Qt::AA_EnableHighDpiScaling);
    }
}
#endif


namespace utils
{
inline constexpr int drow[] = { 1, 0, -1, 0, 1, 1, -1, -1 };
inline constexpr int dcol[] = { 0, 1, 0, -1, 1, -1, 1, -1 };

inline const auto regions = nlohmann::json::parse(std::ifstream("utils/configs/"
                                                                "regions.json"),
                                                  nullptr,
                                                  true,
                                                  true);

inline const auto config = nlohmann::json::parse(std::ifstream("utils/configs/"
                                                               "utils.json"),
                                                 nullptr,
                                                 true,
                                                 true);

template <typename T>
inline void insertVect(std::vector<T> &from, std::vector<T> &to)
{
    to.insert(to.end(), std::make_move_iterator(from.begin()),
              std::make_move_iterator(from.end()));
}

inline void mesureExecutionTime(const std::function<void()> &function)
{
    auto start = std::chrono::high_resolution_clock::now();

    function();

    auto stop = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> time = stop - start;
    std::cout << "Execution time: " << time.count() << " ms" << std::endl;
}

inline cv::Mat getColored(const cv::Mat &mask)
{
    cv::Mat colored = cv::Mat::zeros(mask.size(), CV_8UC3);

    colored.forEach<cv::Vec3b>([&](cv::Vec3b &value, const int *position) {
        auto color =
            regions[std::to_string(mask.at<ushort>(position))]["color"];
        value = { color["blue"], color["green"], color["red"] };
    });

    return colored;
}

inline void showMask(const cv::Mat &mask)
{
    auto colored = getColored(mask);

    cv::namedWindow("mask", cv::WINDOW_NORMAL);
    cv::imshow("mask", colored);
    cv::waitKey();
}

inline bool isSubregion(uint identifier, uint value)
{
    uint dif = value - identifier;
    uint nulls = 0;
    while (identifier % 10 == 0)
    {
        identifier /= 10;
        nulls++;
    }

    return dif < pow(10, nulls);
}


inline void standardize(std::string &string, int length)
{
    string.resize(length);
    for (auto &c : string)
    {
        if (c == 0)
        {
            c = ' ';
        }
    }
}

inline std::string standardizeTime(int time)
{
    if (time < 10)
    {
        return '0' + std::to_string(time);
    }
    return std::to_string(time);
}


inline void log(const std::string &program,
                bool status,
                const std::string &message = "")
{
    const std::string path = config["logs"]["path"];
    if (!std::filesystem::exists(path))
    {
        std::ofstream file(path);
        file << "DATE" << std::string(26, ' ') << "FILE"
             << std::string((int)config["logs"]["fileLength"] - 3, ' ')
             << "STATUS      MESSAGE" << std::endl;
        file.close();
    }
    std::ofstream file(path, std::ios_base::app | std::ios_base::out);
    std::time_t t = std::time(0);
    std::tm *time = std::localtime(&t);
    std::string date =
        std::to_string(time->tm_year + 1900) + '-' +
        standardizeTime(time->tm_mon + 1) + '-' + standardizeTime(time->tm_mday) +
        ' ' + standardizeTime(time->tm_hour) + ':' +
        standardizeTime(time->tm_min) + ':' + standardizeTime(time->tm_sec);
    standardize(date, 30);

    std::string name = program;
    standardize(name, config["logs"]["fileLength"]);
    file << date << name << ' ' << status << "           " << message << std::endl;
    file.close();
}
} // namespace utils
