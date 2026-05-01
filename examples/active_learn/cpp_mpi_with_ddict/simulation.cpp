#include <stdexcept>
#include <cstdlib>
#include <numbers>
#include <random>
#include <optional>
#include <mpi.h>
#include <dragon/serializable.hpp>
#include <dragon/dictionary.hpp>
#include <dragon/return_codes.h>

static timespec_t TIMEOUT = {0,5000000000};
static size_t N_SAMPLES_PER_RANK = 8;

int main(int argc, char** argv) {
    // Initialize the MPI environment
    MPI_Init(NULL, NULL);

    // Get the number of processes
    int world_size;
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);

    // Get the rank of the process
    int world_rank;
    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);

    char* ddict_descriptor = getenv("ROSE_DDICT_DESCRIPTOR");

    if (ddict_descriptor == nullptr) {
      throw std::runtime_error("DDict descriptor not found. Ensure that the environment variable 'ROSE_DDICT_DESCRIPTOR' is set.");
    }

    // Create the connection to the existing DDct
    dragon::DDict<dragon::Serializable, dragon::Serializable> dd_iface(ddict_descriptor, &TIMEOUT);

    // Retrieve the iteration count of the active learning loop
    dragon::SerializableString iter_key("sim_meta_iter_count");
    int iteration = 0;
    if (dd_iface.contains(iter_key)) {
        SerializableInt iter_result = dd_iface[iter_key];
        iteration = iter_result.getVal();
    }
    int previous_iteration = iteration - 1;

    // Initialize the random number generators
    unsigned seed = world_rank + iteration*world_size;
    std::default_random_engine rng(seed);
    std::normal_distribution<double> noise_dist(0.0, 0.1);
    std::uniform_real_distribution<double> query_dist(0.0, 2*std::numbers::pi);

    // Check to see if we should initialize with random points, or use points from the active learner
    std::vector<double> X_local;
    if (previous_iteration >= 0) {
        dragon::SerializableString query_key("query_points_iter_" + std::to_string(previous_iteration));
        if (dd_iface.contains(query_key)) {
            SerializableDoubleVector d_result = dd_iface[query_key];
            X_local = d_result.getVal();
        }
        else
        {
          throw std::runtime_error("Query points not found in DDict.");
        }
    }
    {
      for (size_t i = 0; i < N_SAMPLES_PER_RANK; i++) {
        X_local.push_back(query_dist(rng));
      }
    }

    // Create the simulated "y" vector variable
    std::vector<double> y_local;
    for (size_t i=0; i < X_local.size(); i++) {
      y_local.push_back(sin(X_local[i])*sin(5.*X_local[i]) + noise_dist(rng));
    }

    // Store the results in the DDict
    dragon::SerializableString result_key_X("sim_rank_" + std::to_string(world_rank) + "_iter_" + std::to_string(iteration) + "_X");
    dragon::SerializableString result_key_y("sim_rank_" + std::to_string(world_rank) + "_iter_" + std::to_string(iteration) + "_y");

    dragon::SerializableDoubleVector d_X_local(X_local);
    dragon::SerializableDoubleVector d_y_local(y_local);

    dd_iface[result_key_X] = d_X_local;
    dd_iface[result_key_y] = d_y_local;

    // Increase the loop counter for the number of times the simulation has been called
    MPI_Barrier(MPI_COMM_WORLD);
    if (world_rank == 0){
      dragon::SerializableString iter_count_key("sim_meta_iter_count");
      dragon::SerializableInt iter_count_val(iteration + 1);
      dd_iface[iter_count_key] = iter_count_val;
    }
    MPI_Finalize();
}